# Go module

Status: specification and implementation for the module in `go/`,
published by the `go/v*` tags that `.github/workflows/publish.yml` pushes.

## 1 Goals

1. Embed Small Python in a Go program with `go get` alone: no C library to
   install, no `pkg-config`, only the C compiler cgo already needs.
2. Keep the engine plain C11 that knows nothing of Go. The module compiles
   the same files the Makefile does.
3. Offer the two ways in of the Rust crates (`rust.md`): the engine in the Go
   process, for trusted code, and the engine in a worker process
   (`protocol.md`), for untrusted code.
4. Follow Go's conventions: errors as values, the garbage collector for
   references, `any` and reflection for conversion, as `encoding/json` does.

Not goals: a system-library mode, `context.Context` cancellation, or MSVC
builds.

## 2 Packages

The module `github.com/soasme/small-python/go` has two packages.

| Package | Role |
|---|---|
| `spy` | The C sources, the cgo bindings, and a Go API over them: the engine in this process. |
| `worker` | The parent side of the worker protocol, in pure Go. It runs a `spy-worker` executable. |

Go has no build scripts, so the split of the Rust crates into sources,
raw bindings, and a safe API collapses into one cgo package: cgo compiles
every C file in the package directory. `spy.c`, `spy-std.c`, and the
headers they include are copied there by `make go-vendor`; they are ignored
by git on `main` and committed only in the release commit a `go/v*` tag names
(§6), as `make rust-vendor` fills `small-python-src`. Go's build cache hashes
only the files of a package's directory, so a cgo file including the
checkout's sources by a relative path would miss edits to them. The licenses
of the tables the engine carries are copied to `go/LICENSE` and
`go/licenses/`.

`bridge.c` holds the one C file written for Go: it adapts the engine's
callback types to the functions `spy` exports, passing `cgo.Handle` values
through the `void *` slots as `uintptr_t`.

## 3 `spy`

```go
rt, err := spy.New()
if err != nil {
	return err
}
defer rt.Close()
rt.Define("add", func(rt *spy.Runtime, args spy.Args) (any, error) {
	var a, b int
	if err := args.Scan(&a, &b); err != nil {
		return nil, err
	}
	return a + b, nil
})
n, err := spy.As[int](rt.Eval("add(40, 2)")) // 42
```

### 3.1 Runtime

`Runtime` owns one `SPYContext`. `New` registers the standard layer
(`spy_std_init`); `NewBare` has only the core and its `builtins`. Both send
output to `os.Stdout`, as `worker` and the Python package do; the engine
itself has no default and raises `OSError` from `print` without one.

| Method | C API |
|---|---|
| `Eval(source)`, `Exec(source)` | `spy_eval`, `spy_exec`, filename `<string>` |
| `Get(name)`, `Set(name, value)` | `spy_get_global`, `spy_set_global` |
| `Function(name, f)`, `Define(name, f)` | `spy_native` with a release callback, then `spy_set_global` |
| `RegisterModule(name, init)`, `ExecModule(module, source, filename)` | `spy_new_module`, `spy_exec_module` |
| `SetOutput(w)`, `SetLoader(f)` | `spy_set_output` with an `io.Writer`, `spy_set_module_loader` |
| `Mount(directory, path, readOnly)` | `spy_mount`; an empty `path` is `NULL` |
| `SetStepLimit(n)`, `SetOptimize(level)`, `Collect()` | the same names |
| `ToValue(x)` | the conversions of §3.3 |
| `Close()` | `spy_context_free` |

A runtime is not safe for concurrent use, as most Go types; it may move
between goroutines, since a context holds no thread-affine state. A host
function receives the runtime it runs in. `Close` frees the context; every
later operation on the runtime or its values returns `ErrClosed`.

### 3.2 Values

`*Value` holds one reference to an engine value. Go has no destructors, so
`runtime.AddCleanup` queues the reference when the value becomes
unreachable, and the runtime releases the queue on the goroutine of its next
call into the engine: the context is never touched by the collector's
goroutine. After `Close` the queue is dropped, because `spy_context_free`
frees every value itself.

Its methods are `Decode`, `GetAttr`, `SetAttr`, `GetItem`, `SetItem`,
`Call`, `CallKeywords`, `Iter` (an `iter.Seq2[*Value, error]`), `Truth`,
`IsNone`, `Repr`, and `Str`; `String` is `str(value)` for `fmt`. The generic
`As[T](v, err)` decodes an operation's result, passing its error on. A value
passed to another runtime is refused with `ValueError`.

### 3.3 Conversion

`ToValue` converts in by reflection; `Decode` converts out into what a
pointer points to.

| Go | Engine |
|---|---|
| `nil`, a nil pointer | `None` |
| `bool` | `bool` (out: only a `bool`) |
| integers | `int`; beyond `int64` or the target's range: `OverflowError` |
| `float32`, `float64` | `float` (out: as `float(x)` accepts) |
| `string` | `str`; a lone surrogate keeps its three-byte form, which a Go string can hold |
| `[]byte` | `bytes` (out: also `bytearray`) |
| `spy.Tuple` | `tuple` |
| other slices and arrays | `list`; out: any iterable, of exactly the array's length |
| maps | `dict` in sorted key order; out: any mapping, by its keys |
| structs | `dict` of the exported fields, named by a `spy:"name"` tag, `spy:"-"` skipping one; out: any mapping, ignoring unknown keys |
| pointers | what they point to; out: `None` is a nil pointer |
| `*Value` | itself |
| `spy.Func` | a builtin function |

Decoding into an `any` gives `nil`, `bool`, `int64`, `float64`, `string`,
`[]byte`, `[]any` for a list, `spy.Tuple`, and `map[any]any` for a dict,
and a `*Value` for anything else, including a dict key that is not
comparable in Go. A host function's `Args` holds the positional arguments
and the keyword arguments as a `map[string]*Value`; `Args.Scan(&a, &b)`
decodes the positional ones after checking their count, as
`database/sql`'s `Rows.Scan` does.

### 3.4 Errors

`*Exception{Type, Message, Filename, Line}` is an exception in either
direction. An engine exception that escapes is copied out and cleared;
`Message` is `spy_error_display`'s text. A host function or module init
returning an error raises a new exception (`spy_error`): an `*Exception`,
found with `errors.As`, keeps its type and message, as one from `Raise`
does; any other error raises `RuntimeError` with its text. No panic reaches
C: in a host function or a module init it raises `RuntimeError`, in the
output writer it fails the write, and in the loader it counts as no source.
Source containing NUL raises `SyntaxError`; a name containing NUL raises
`ValueError`.

### 3.5 Trust

As `rust.md` §3.5: the engine runs in the Go process. Use `spy` for code
you trust; for anything else use `worker`.

## 4 `worker`

The Go counterpart of the Python package (`python.md`) and the
`small-python-worker` crate, on the same worker and protocol.

```go
rt, err := worker.New(worker.Options{Timeout: 5 * time.Second, MemoryLimit: 64 << 20})
if err != nil {
	return err
}
defer rt.Close()
rt.Define("greet", func(rt *worker.Runtime, args []any, kwargs map[string]any) (any, error) {
	if name, ok := args[0].(string); ok && len(args) == 1 {
		return "hello " + name, nil
	}
	return nil, worker.Raise("TypeError", "greet(name)")
})
v, err := rt.Eval("greet('spy')") // "hello spy"
```

### 4.1 The worker executable

The package runs the `spy-worker` the repository builds, found on `$PATH`
(`make install` installs it) or named by `Options.Worker`. It is not
embedded, because Go has no build scripts to compile it (§7).

### 4.2 Runtime

`New(Options)` starts the worker as `protocol.md` §9 describes (empty
environment, working directory `/`, its own process group, only descriptors
0 to 2) and sends `INIT`. The zero `Options` is the default: `Bare` leaves
out the standard layer, `StepLimit`, `MemoryLimit`, and `Timeout` are
unlimited at 0, `MessageLimit` 0 is 64 MiB, `Output` nil is `os.Stdout`,
and `Loader` nil answers no module.

| Method | Message |
|---|---|
| `Eval(source)`, `Exec(source)` | `EVAL`, `EXEC` |
| `Call(function, args, kwargs)` | `CALL`; `function` is a global name, an `*Object`, or a `*Function` |
| `Get(name)` | `GET`; `ok` is false for a `NameError` |
| `Set(name, value)`, `Delete(name)` | `SET`, `DELETE` |
| `Function(name, f)`, `Define(name, f)` | none, then `SET` |
| `RegisterModule(name, members, source)` | `MODULE` |
| `Mount(directory, path, readOnly)` | `MOUNT`, after resolving `directory` |
| `Collect()` | `COLLECT` |
| `GetAttr`, `SetAttr`, `GetItem`, `SetItem`, `Len`, `Contains`, `Iter`, `Next`, `Truth`, `Hash`, `Compare`, `Repr`, `Str`, `Dir` | `OP` 1 to 19; `Next`'s `ok` is false at `StopIteration` |
| `Version()`, `Pid()`, `Closed()`, `Close()` | the `INIT` reply, the process id, state, closing |

A runtime is not safe for concurrent use. A host function is
`func(rt *Runtime, args []any, kwargs map[string]any) (any, error)`; through
the runtime it receives it may make nested requests, but `Eval` and `Exec`
return an error matching `ErrInvalid` there. `Close` closes the worker's
input and waits up to a second for it to exit.

### 4.3 Values

Values cross as Go values, one per row of `protocol.md` §4: `nil`, `bool`,
`int64` or `*big.Int`, `float64`, `complex128`, `string`, `[]byte`,
`ByteArray`, `[]any` (list), `Tuple`, `Set`, `FrozenSet`, `Dict` (items in
order), `*Object`, and `*Function`. Sending also accepts the other integer,
float, and complex types and `map[string]any`, in sorted key order; any
other type fails with `TypeError` before sending. Sets and dicts are kept as
sequences, so the parent never hashes what the worker sends. A `str`
holding a lone surrogate keeps its three-byte form in the Go string and
round-trips unchanged; a string that is not UTF-8 in that sense fails with
`UnicodeEncodeError` before sending.

`*Object` is a handle to an engine value. When the garbage collector finds
one unreachable, its id is queued and released with the next message
(`RELEASE`). Objects are equal when they are the same pointer.

### 4.4 Errors

| Type | Meaning |
|---|---|
| `*Exception` | An engine exception escaped: `Type`, `Message`, `Filename`, `Line`, `Object` (an `*Object`), and `Cause`, which `Unwrap` returns. |
| `*WorkerError` | The worker was lost (`protocol.md` §8); `State` is its `*os.ProcessState` when it exited on its own. |
| `*TimeoutError` | The operation ran past the timeout; the engine stopped it and the runtime stays open, unless the worker did not stop within the grace period and was terminated. |
| matches `ErrInvalid` | Misuse: a closed runtime, a value of another runtime, a message over the limit, `Eval` in a host function. |

A host function's error becomes the failure of `protocol.md` §7.4: an
`*Exception` carrying an object of this runtime re-raises it unchanged;
another `*Exception` raises its type name (the builtin class, else
`RuntimeError`); an error matching `ErrInvalid` raises `ValueError`, and
any other error `RuntimeError`, with the error's text. If that exception
escapes, the resulting `*Exception` holds the original error as its
`Cause`, so `errors.Is` finds it. A panic in a host function terminates the
worker and goes on panicking. Once lost, every request returns the same
error.

### 4.5 Timeouts

The worker stops an operation at its timeout itself (`protocol.md` §10),
and the runtime stays open. Two goroutines per runtime move bytes: one
reads frames, checking each length against the limit before allocating,
and one writes. The parent waits for the reader, and for room in the
writer's queue, until the timeout plus a grace period of one second, so
neither a silent worker nor one that stops reading can block it longer;
such a worker is terminated. Time spent in host functions, the loader, and
output extends the deadline.

### 4.6 Security

As `rust.md` §4.6.

## 5 Building and testing

```sh
make test-go               # go vet and go test in go/, after the two below
make go-vendor             # copy the C sources into go/spy
make spy-worker            # the worker the worker tests run
```

The tests cover conversion in both directions, structs and maps, exceptions
and their lines, host functions with errors, keywords, and panics, modules,
the loader and output, limits, values of another runtime, closed runtimes,
and values the garbage collector releases; for the worker, the ports of the
Rust crate's tests: nested callbacks, causes, object operations and handle
release, a timeout that excludes host time, workers killed by `SIGSEGV`,
`SIGABRT`, and `SIGKILL`, a panicking host function, and the sealed sandbox
on macOS. They pass under `go test -race`.

## 6 Publishing

A Go module is published by a tag. The module's version is the engine's.
Pushing a version tag `vX.Y.Z` runs the `go` job of
`.github/workflows/publish.yml`: it runs `make test-go`, then commits the
output of `make go-vendor` on top of the tagged commit and tags that commit
`go/vX.Y.Z`, which is the tag form Go requires for a module in a
subdirectory. `main` never carries the copies. A tag that exists is left
alone.

## 7 Alternatives considered

1. **The module at the repository root.** The cgo files could include the
   checkout's `spy.c` by path, with no copies. But every `go get` would then
   download the whole repository, and Go's build cache would not see edits
   to files outside the package directory.
2. **Copies committed on `main`.** As `go-sqlite3` commits SQLite. Every
   engine change would then be committed twice.
3. **Running the program's own executable as the worker**, with a cgo
   constructor that serves the protocol before the Go runtime starts, as
   runc's `nsexec` does. It would make the worker installable with `go get`
   alone, but the process would map the whole Go program under the sandbox,
   and the in-process engine and the worker's counting-allocator engine
   define the same symbols, so a program could not import both packages.
4. **Explicit `Free` on values.** Lifetimes cannot be checked in Go, so a
   forgotten `Free` leaks and an early one crashes. The collector's cleanups
   with a queue drained on the runtime's own goroutine are safe either way.
