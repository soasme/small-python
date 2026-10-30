# Rust crates

Status: specification and implementation for the crates in `rust/`,
published to crates.io by `.github/workflows/publish.yml`.

## 1 Goals

1. Embed Small Python in a Rust program with `cargo add` alone: no C library
   to install, no system package, no `pkg-config`.
2. Keep the engine plain C11 that knows nothing of Rust. The crates compile
   the same files the Makefile does.
3. Offer two ways in, as the Python package's history did: the engine in the
   Rust process, for trusted code and the lowest overhead, and the engine in
   a worker process (`protocol.md`), for untrusted code.
4. Make ownership mistakes compile errors rather than crashes in the safe
   API.

Not goals: a system-library mode that links an installed `libspy.a`, async
APIs, or MSVC builds (the engine needs C11 complex numbers, which MSVC lacks).

## 2 Crates

The layout follows `mlua`, whose `mlua-sys` builds Lua from the `lua-src`
crate with `cc` and whose `mlua` crate wraps it safely.

```text
small-python ──> small-python-sys ──build──> small-python-src ──> cc
small-python-worker ─────────────────build──> small-python-src ──> cc
```

| Crate | Role |
|---|---|
| `small-python-src` | The C sources, and a `cc::Build` configured for them (C11, include path). A build dependency only. |
| `small-python-sys` | Raw bindings to `spy.h` and `spy-std.h`, written by hand. Its build script compiles `spy.c` and `spy-std.c` into a static library; `links = "spy"`. |
| `small-python` | A safe API over `small-python-sys`: the engine in this process. |
| `small-python-worker` | The parent side of the worker protocol. Its build script compiles and links `spy-worker`, which the crate embeds. |

`small-python-src` finds the sources in the repository checkout two
directories up; a published crate carries a copy in `csrc/` instead, with
the Unicode and Python licenses, made by `make rust-vendor`. Each build
compiles the C with the target's C compiler at the Cargo profile's
optimization level; `cargo` users tune it with profile overrides as for any
`cc` crate. On Windows the GNU targets (`x86_64-pc-windows-gnu`) build; an
MSVC-like compiler stops the build with that explanation.

## 3 `small-python`

```rust
use small_python::{Runtime, Result};

fn main() -> Result<()> {
    let rt = Runtime::new()?;
    rt.define("add", |rt, args| {
        let (a, b): (i64, i64) = args.extract()?;
        rt.to_py(a + b)
    })?;
    let n: i64 = rt.eval("add(40, 2)")?;
    assert_eq!(n, 42);
    Ok(())
}
```

### 3.1 Runtime

`Runtime` owns one `SPYContext`. `Runtime::new()` registers the standard
layer (`spy_std_init`); `Runtime::bare()` has only the core and its
`builtins`. Every method takes `&self`:

| Method | C API |
|---|---|
| `eval::<T>(source)`, `exec(source)` | `spy_eval`, `spy_exec`, filename `<string>` |
| `get::<T>(name)`, `set(name, value)` | `spy_get_global`, `spy_set_global` |
| `function(name, f)`, `define(name, f)` | `spy_native` with a release callback, then `spy_set_global` |
| `register_module(name, init)`, `exec_module(module, source, filename)` | `spy_new_module`, `spy_exec_module` |
| `set_output(f)`, `set_loader(f)` | `spy_set_output`, `spy_set_module_loader` |
| `mount(directory, path, read_only)` | `spy_mount` |
| `set_step_limit(n)`, `set_optimize(level)`, `collect()` | the same names |
| `to_py(value)` | the conversions of §3.3 |
| `ctx()` | the raw context, for calls into `small_python::ffi` |

A runtime is `Send` and not `Sync`: a context holds no thread-affine state,
and every closure stored with it must be `Send`. Dropping the runtime frees
the context and then the closures.

### 3.2 Values

`Value<'rt>` owns one reference to an engine value and borrows the runtime
it came from, so no value outlives its context, which `spy_context_free`
requires. `Clone` retains, `Drop` releases. Its methods are `extract`,
`getattr`, `setattr`, `get_item`, `set_item`, `call`,
`call_with_keywords`, `iter` (an `Iterator` of `Result<Value>`), `truth`,
`repr`, `str`, `is_none`, `kind` (the `SPY_*` type tag), and `as_ptr` /
`into_raw` / `from_raw` for the C API. `Debug` and `Display` use `repr` and
`str`. A value passed to another runtime is refused with `ValueError`.

### 3.3 Conversion

`IntoPy` converts Rust values in; `FromPy<'rt>` converts out.

| Rust | Engine |
|---|---|
| `()` | `None` |
| `bool` | `bool` (out: only a `bool`) |
| integers, 8 to 128 bits | `int`; out of `i64` or the target's range: `OverflowError` |
| `f32`, `f64` | `float` (out: as `float(x)` accepts) |
| `&str`, `String`, `char` | `str`; out: a `str` with a lone surrogate raises `UnicodeEncodeError` |
| `Option<T>` | `None` or `T` |
| `Vec<T>`, `&[T]` | `list`; out: any iterable |
| `HashMap`, `BTreeMap` | `dict`; out: any mapping, by its keys |
| tuples up to 8 | `tuple`; out: an iterable of that length |
| `Value` | itself |

Call arguments are `IntoArgs`: `()`, a tuple, or a `Vec`. A host function
receives `Args`, whose `extract::<T>()` converts the positional arguments to
a tuple (checking their count) or a `Vec`, and whose `keyword(name)` reads a
keyword argument.

With the `serde` feature, `Runtime::to_value(&T)` and
`Runtime::from_value::<T>(&value)` follow serde_json's data model: structs
and maps are dicts, sequences are lists, unit and `None` are `None`, a unit
variant is its name, and a variant with data is a dict of one entry naming
it. Engine `bytes` deserialize as a byte buffer.

### 3.4 Errors

`Error { type_name, message, filename, line }` is an exception in either
direction. An engine exception that escapes is copied out and cleared;
`message` is `spy_error_display`'s text. A host function or module init
that returns `Err` raises a new exception with that type name and message
(`spy_error`), so an engine exception passing through Rust keeps its type and
message but not its identity. No panic reaches C: in a host function or a
module init it raises `RuntimeError`, in the output callback it fails the
write, and in the loader it counts as no source. Source containing NUL raises
`SyntaxError`, as CPython's `compile` does; a name containing NUL raises
`ValueError`.

### 3.5 Trust

The engine runs in the Rust process. A memory-safety bug in it, or in code
that exploits one, is a bug in the program. Use `small-python` for code you
trust; for anything else use `small-python-worker`.

## 4 `small-python-worker`

The Rust counterpart of the Python package (`python.md`), on the same worker
and protocol.

```rust
use small_python_worker::{Error, Runtime, Value};
use std::time::Duration;

let mut rt = Runtime::builder().timeout(Duration::from_secs(5)).memory_limit(64 << 20).spawn()?;
rt.define("greet", |_, args, _| match &args[..] {
    [Value::Str(name)] => Ok(format!("hello {name}").into()),
    _ => Err(Error::python("TypeError", "greet(name)")),
})?;
assert_eq!(rt.eval("greet('spy')")?, Value::from("hello spy"));
```

### 4.1 The worker executable

The build script compiles `spy-worker.c` twice, as the engine with
`SPY_WORKER_ENGINE` and as the worker, and links them with the target's C
compiler (`-static` on Windows). The crate embeds the executable. On first
use in a process it is written to `small-python/spy-worker-<version>-<hash>`
in the user's cache directory (`~/Library/Caches` on macOS, `$XDG_CACHE_HOME`
or `~/.cache` elsewhere on Unix, `%LOCALAPPDATA%` on Windows, else the
temporary directory), by writing a temporary file with mode `0700` and
renaming it into place; an existing file is used only if its bytes equal the
embedded ones. `Builder::worker(path)` runs a given executable instead, for
deployments without a writable cache.

### 4.2 Runtime

`Runtime::builder()` takes `std`, `step_limit`, `memory_limit`, `timeout`,
`message_limit`, `output`, `loader`, and `worker`, with the defaults and
meaning of the Python package's arguments (`python.md` §3.1); `spawn()`
starts the worker as `protocol.md` §9 describes (empty environment, working
directory `/`, its own process group, only descriptors 0 to 2) and sends
`INIT`. `Runtime::new()` uses the defaults.

| Method | Message |
|---|---|
| `eval(source)`, `exec(source)` | `EVAL`, `EXEC` |
| `call(function, args, kwargs)` | `CALL`; `function` is a global name, an `Object`, or a `Function` |
| `get(name)` | `GET`; `None` for a `NameError` |
| `set(name, value)`, `delete(name)` | `SET`, `DELETE` |
| `function(name, f)`, `define(name, f)` | none, then `SET` |
| `register_module(name, members, source)` | `MODULE` |
| `mount(directory, path, read_only)` | `MOUNT`, after resolving `directory` |
| `collect()` | `COLLECT` |
| `getattr`, `setattr`, `get_item`, `set_item`, `len`, `contains`, `iter`, `next`, `truth`, `hash`, `compare`, `repr`, `str`, `dir` | `OP` 1 to 19; `next` returns `None` at `StopIteration` |
| `version()`, `id()`, `is_closed()`, `close()` | the `INIT` reply, the process id, state, closing |

Every method takes `&mut self`, so overlapping use is a compile error, and a
runtime is `Send`. A host function is
`Fn(&mut Runtime, Vec<Value>, Vec<(String, Value)>) -> Result<Value>` and
`Send + Sync`; through the runtime it receives it may make nested requests,
but `eval` and `exec` return `Error::Invalid` there. `close()` closes the
worker's input and waits up to a second for it to exit; dropping a runtime
terminates the worker at once.

### 4.3 Values

`Value` is an enum with one variant per row of `protocol.md` §4: `None`,
`Bool`, `Int` (`i64`), `BigInt` (the protocol's hex spelling), `Float`,
`Complex`, `Str`, `Bytes`, `ByteArray`, `List`, `Tuple`, `Set`, `FrozenSet`,
`Dict` (pairs in order), `Object`, and `Function`. Sets and dicts are kept as
sequences, so the parent never hashes what the worker sends. A `str` holding
a lone surrogate arrives with U+FFFD in its place. `From` builds values from
common Rust types; `as_bool`, `as_int`, `as_float`, `as_str`, `as_slice`,
and `get` read them.

`Object` is a handle to an engine value. Clones share the handle; when the
last is dropped its id is queued, from any thread, and released with the
next message (`RELEASE`). Objects are equal when they are the same handle.

### 4.4 Errors

| Variant | Meaning |
|---|---|
| `Python(PythonError)` | An engine exception escaped: `type_name`, `message`, `filename`, `line`, `exception` (an `Object`), and `cause`. |
| `Worker { message, status }` | The worker was lost (`protocol.md` §8); `status` is its exit status, negative for a signal. |
| `Timeout(duration)` | The operation ran past the timeout; the worker was terminated. |
| `Host(error)` | A host function's Rust error. |
| `Invalid(message)` | Misuse: a closed runtime, a value of another runtime, a message over the limit, `eval` in a host function. |

A host function's `Err` becomes the failure of `protocol.md` §7.4: a
`Python` error carrying an exception of this runtime re-raises it unchanged;
another `Python` error raises its type name (the builtin class, else
`RuntimeError`); `Invalid` raises `ValueError` and anything else
`RuntimeError`, with the error's text. If that exception escapes, the
resulting `PythonError` holds the original error as its `cause`, which is
also its `source()`. A panic in a host function terminates the worker and
continues unwinding. Once lost, every request returns the same loss.

### 4.5 Timeouts

Two threads per runtime move bytes: one reads frames, checking each length
against the limit before allocating, and one writes. The parent waits for
the reader with the operation's deadline, so neither a silent worker nor one
that stops reading can block it past the timeout. Time spent in host
functions, the loader, and output extends the deadline.

### 4.6 Security

As `python.md` §4: the process boundary is the isolation boundary, and the
worker seals itself under the OS sandbox before it first runs code; a later
`mount` fails with `PermissionError`. The parent validates every message and
never trusts a length, count, depth, id, or integer spelling it has not
checked.

## 5 The todo example

`examples/todo`, beside the C examples and outside the crates' workspace,
uses the published `small-python` from crates.io, at the version the
release bump gives every package. It is a todo list written like a Flask application (`app.py`) and served by a
Rust host that knows nothing about todos. The host supplies what the engine
lacks: axum and tokio serve and route, serde_json becomes the module `json`
(`loads` and `dumps`, through the `serde` feature), and `app.py`'s directory
is mounted read-only for `open()`. `web.py`, built into the host and
registered with `register_module`, turns these into `App` with route
decorators, `request`, and `abort`. After running `app.py` the host reads
`web.routes` and gives each method and path an axum route calling
`web.dispatch`, which returns the status, content type, and text. One
`Runtime` behind a `Mutex` serves every request in turn.

```sh
cd examples/todo
cargo run                  # http://127.0.0.1:3000; APP_DIR and ADDRESS change the app and address
curl -d '{"title":"write docs"}' localhost:3000/todos
```

## 6 Building, testing, publishing

```sh
make test-rust             # cargo test in rust/ (all features), and examples/todo on these crates
make rust-vendor           # copy the C sources into rust/small-python-src/csrc
```

The tests cover conversion in both directions, exceptions and their lines,
host functions with errors, keywords, and panics, modules, the loader and
output, limits, values of another runtime, moving a runtime between threads,
and serde round trips; for the worker, nested callbacks, causes, object
operations and handle release, a timeout that excludes host time, workers
killed by `SIGSEGV`, `SIGABRT`, and `SIGKILL`, a panicking host function,
and the sealed sandbox on macOS; and the todo application's routes, aborts,
and page.

The crates share the engine's version. Pushing a version tag runs the
`crates` job of `.github/workflows/publish.yml`: it checks the tag against
the crate version, runs `make test-rust` and `make rust-vendor`, publishes
`small-python-src`, `small-python-sys`, `small-python`, and
`small-python-worker` in that order, skipping any version already on
crates.io, and then tests `examples/todo` on the published crates. Before
the release, only the checkout satisfies the example's dependency, so
`make test-rust` patches it in, and the example commits no `Cargo.lock`. It authenticates with the `CARGO_REGISTRY_TOKEN` secret of the
`crates-io` environment when one is set, which the first release needs
because crates.io trusts a workflow only for crates that exist, and with
trusted publishing otherwise. `cargo publish --workspace --dry-run` checks
the packages locally.

## 7 Alternatives considered

1. **bindgen.** Generating the bindings at build time needs libclang on every
   user's machine. `spy.h` is small and stable, so the bindings are written by
   hand, as `mlua-sys` does.
2. **Sources in `small-python-sys` only.** The worker crate would then build
   the in-process engine it never links, doubling the C compile. A separate
   source crate is what `lua-src` is to `mlua`.
3. **A system library.** Linking an installed `libspy.a` would need a
   matching header and build flags; until a distribution ships one, the
   vendored build is the only mode.
4. **Running the worker from the program's own executable.** It avoids
   writing a file, but every program would have to call a hook first thing
   in `main`, and the sandbox would cover a process holding the program's
   whole address space. The embedded executable is the same file the Python
   package ships.
5. **Lifetime-free values.** Reference-counting the runtime, as `mlua` 0.10
   does, makes values `'static` but the runtime `!Send` unless guarded by a
   lock. Borrowed values cost a lifetime parameter and keep the runtime
   `Send` with no lock.
