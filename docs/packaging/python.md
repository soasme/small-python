# Python package

Status: specification for `small-python` on PyPI. It replaces the in-process
CPython extension (`small_python._core`), which this design retires.

## 1 Goals

1. Run untrusted code, including code written by a language model, from
   CPython. Nothing the engine does, including a memory-safety bug triggered
   on purpose, may crash, hang, or take over the CPython process.
2. Give engine code exactly the host functions, modules, and directories the
   embedder grants, and nothing else.
3. Keep the embedding API of the retired extension where the design allows,
   so that existing code keeps working.
4. Ship one wheel per platform that works on every supported CPython.

Not goals: sharing Python objects with engine code, running engine code
concurrently in one runtime, or protecting the engine from its host.

## 2 Architecture

Each `Runtime` starts one `spy-worker` process (`protocol.md`) and speaks the
worker protocol over its stdin and stdout. The package is pure Python plus the
worker executable; it links no C into CPython.

```text
CPython process                               spy-worker process
+----------------------------+   pipe         +------------------------+
| small_python.Runtime       | ---requests--> | SPYContext             |
|   host functions, loader,  | <--requests--- |   engine, std modules, |
|   output, Object proxies   |                |   handle table         |
+----------------------------+                +------------------------+
```

Package layout:

```text
small_python/
  __init__.py      Runtime, Object, Error, WorkerError, Timeout, versions
  _wire.py         value codec and message framing (protocol.md §3–§4)
  _runtime.py      the parent side: turns, handles, host callbacks
  _runtime.pyi     types
  spy-worker       the worker executable for this platform
  py.typed
```

The wheel is tagged `py3-none-<platform>`: it holds no extension module, so
one wheel serves CPython 3.10 and later. Wheels are built for manylinux and
musllinux (x86_64, aarch64) and macOS (x86_64, arm64). An sdist builds the
worker with the system C compiler.

## 3 API

```python
from small_python import Runtime, Object, Error, WorkerError, Timeout
```

### 3.1 `Runtime`

```python
Runtime(*, std=True, step_limit=0, memory_limit=0, timeout=None,
        output=None, loader=None, message_limit=64 << 20)
```

Starting a runtime starts its worker and waits for its `INIT` reply. If the
worker cannot start, the constructor raises `WorkerError`.

| Argument | Meaning |
|---|---|
| `std` | Register the standard modules (`sys`, `gc`, `weakref`, ...). |
| `step_limit` | Evaluation steps per top-level `eval` or `exec`; `0` is unlimited. Exceeding it raises `RuntimeError` in the engine. |
| `memory_limit` | Bytes the engine may hold; `0` is unlimited. Exceeding it raises `MemoryError` in the engine. |
| `timeout` | Seconds a single operation may spend running in the worker, or `None`. Exceeding it terminates the worker and raises `Timeout`. |
| `output` | Callable receiving printed text; `None` writes to `sys.stdout`. |
| `loader` | Callable mapping a module name to source `str`, or `None` when there is none. |
| `message_limit` | Largest message in bytes, either direction. |

Negative limits, a non-positive `timeout`, or a non-callable `output` or
`loader` raise `ValueError` or `TypeError` before the worker starts.

Running code:

- `eval(source, filename="<string>")` returns the value of the last expression
  statement, or `None`.
- `exec(source, filename="<string>")` returns `None`.
- `call(function, /, *args, **kwargs)` calls a global name (`str`), an
  `Object`, or a Python callable (which is first passed into the engine as a
  native function), and returns the converted result.

Globals:

- `rt[name]` reads a global, falling back to builtins; `KeyError` when absent.
- `rt[name] = value` sets a global; `TypeError` when `value` does not convert.
- `del rt[name]` deletes a global; `KeyError` when absent.

Extending:

- `define(name, function)` binds a callable as the global `name`; returns
  `function`.
- `function(func=None, *, name=None)` is the decorator form.
- `register_module(name, members=None, source=None)`: `import name` makes a
  module whose attributes are `members` and then runs `source` in it.
- `mount(directory, path=None, *, read_only=False)`: let `open()` reach
  `directory` at engine path `path` (default: its resolved host path). The
  directory is resolved in the parent; `Error` if it does not exist.

Lifetime:

- `collect()` runs the cycle collector and returns the number freed.
- `close()` ends the worker and drops every host reference. Idempotent.
- `closed` is `True` after `close()` or once the worker is lost.
- The runtime is a context manager that closes on exit, and `__del__` closes
  it as a last resort.

### 3.2 Conversion

Values cross by copy (`protocol.md` §4):

| Python | Engine | Notes |
|---|---|---|
| `None`, `bool`, `int`, `float`, `complex` | same | any size `int` |
| `str`, `bytes`, `bytearray` | same | copied |
| `list`, `tuple`, `dict`, `set`, `frozenset` | same | copied; nesting over 200 levels raises `RecursionError` (an `Error` of that type from the engine) |
| callable | native function | keeps the callable until the runtime closes |
| `Object` | the engine value | from another runtime: `ValueError` |
| anything else | — | `TypeError` |

Python subclasses of these types convert as their base type (an `IntEnum`
member arrives as an `int`, an `OrderedDict` as a `dict`). From the engine,
only values whose type is exactly one of the first three rows come back by
content (`protocol.md` §4); everything else, subclasses included, is an
`Object`.

### 3.3 `Object`

A proxy for an engine value held by the worker. It supports calling,
attribute get and set, item get and set, `len`, `in`, iteration, `next`,
`bool`, `hash`, the six comparisons, `repr`, `str`, and `dir`; each is one
`OP` (`protocol.md` §7.3), and a call is one `CALL`. Protocol failures raise what Python expects:
`AttributeError`, `KeyError` (with the key), `IndexError`, `TypeError`, and
`StopIteration` at the end of iteration; other engine exceptions raise
`Error`. Comparing with a value that does not convert is unequal for `==` and
raises `TypeError` for ordering. Objects of different runtimes are unequal.
Deleting attributes or items raises `TypeError`.

When an `Object` is collected its handle is queued and released with the next
message to the worker. Once its runtime is closed, every operation but `repr`
raises; once the runtime is lost, `WorkerError`.

### 3.4 Exceptions

`Error(Exception)` reports an engine exception that escaped. Attributes:
`type`, `message`, `exception` (an `Object`, or `None`), `filename`, `lineno`;
`str(e)` is `"type: message"`. If it came from a host function's exception
that engine code did not handle, that Python exception is its `__cause__`; a
`BaseException` that is not an `Exception` (`KeyboardInterrupt`, `SystemExit`)
is re-raised itself instead.

`WorkerError(RuntimeError)` reports a lost worker (`protocol.md` §8). Its
message names the cause; `returncode` is the worker's exit status (negative
for a signal) or `None` when it was terminated by the parent.

`Timeout(WorkerError, TimeoutError)` reports an expired timeout.

Misuse raises ordinary exceptions: `RuntimeError` for a closed runtime, for
`eval`/`exec`/`close` inside a callback of the same runtime, and for use from
another thread while the runtime is busy.

### 3.5 Host callbacks

A host function receives converted positional and keyword arguments and
returns a value that converts. While it runs, the worker waits; the host
function may call `call`, `rt[...]`, `define`, and `Object` operations on the
same runtime (nested requests), but not `eval`, `exec`, or `close`.

An exception from a host function becomes an engine exception
(`protocol.md` §7.4): the nearest engine builtin class by name in the
exception's method resolution order, with the same `args` when they convert,
else its message; otherwise `RuntimeError`. An escaping `Error` from the same
runtime re-raises the original engine exception.

The loader follows the same rules. An exception from `output` is reported
with `sys.unraisablehook`, and the engine's `print` raises `OSError`. The loader receives the engine's
probe names: for `import pkg.mod` it is asked for `pkg.mod.__init__` (a
package), then `pkg.mod`; returning source for `pkg.mod.__namespace__` makes a
namespace package. The parent answers the `__init__` and `__namespace__`
probes with `None` unless the loader returns source for them, so a plain
`dict.get` loader works.

### 3.6 Threads

A runtime belongs to one thread at a time: the thread that started its
current top-level operation, until that operation returns. A call from any
other thread meanwhile raises `RuntimeError`. Separate runtimes are
independent and may be used from different threads at once. Releasing
collected objects is safe from any thread.

### 3.7 Signals and interruption

The worker runs in its own process group, so Ctrl-C reaches only CPython. A
`KeyboardInterrupt` that arrives while CPython waits for the worker terminates
the worker, marks the runtime lost, and propagates. A `KeyboardInterrupt`
inside a host function is a host exception (§3.4).

## 4 Security

The process boundary is the isolation boundary. Inside it, the engine
confines code to its grants (`docs/manual.md`); outside it, the parent:

1. starts the worker as in `protocol.md` §9: empty environment, working
   directory `/`, no extra descriptors, its own process group, death with the
   parent;
2. bounds every read by `message_limit`, validates every message before acting
   on it, and terminates the worker on any violation;
3. bounds time per operation with `timeout`;
4. never evaluates, unpickles, or imports anything the worker sends.

A worker that has been taken over by an exploit would run with the user's
operating-system privileges. Containing that is the job of an OS sandbox,
which the worker applies to itself, without privileges, immediately before it
first runs engine code (its first `EVAL`, `EXEC`, `CALL`, or `OP`; see
`protocol.md` §9). Mounts are fixed from then on: a later `mount` raises
`Error` of type `PermissionError`.

| Platform | Layer |
|---|---|
| Linux | `PR_SET_NO_NEW_PRIVS` |
| Linux | Landlock (kernel 5.13 and later): files only beneath the mounted directories, read-only where mounted so; no TCP (kernel 6.7 and later) |
| Linux x86_64, aarch64 | seccomp: only the system calls the engine makes (I/O on open descriptors, memory, clocks, signals to itself, exit, and file calls when directories are mounted); any other fails with `EPERM`; a foreign architecture's calls kill the worker |
| macOS | `sandbox_init` profile: deny by default; allow metadata reads, and reading (and writing, unless read-only) beneath the mounted directories |

A layer the kernel lacks is skipped; one the kernel refuses ends the worker.
Other platforms have no OS layer; for hostile code there, also run the parent
in a container.

## 5 Compatibility with the retired extension

Unchanged: `Runtime` methods and arguments, conversion, `Object` operations,
`Error` attributes and causes, callback rules.

Changed:

1. Engine code runs in another process; a crash raises `WorkerError` instead
   of killing CPython.
2. New arguments `memory_limit`, `timeout`, `message_limit`; new exceptions
   `WorkerError` and `Timeout`.
3. Engine subclasses of the convertible types (a `dict` subclass defined in
   engine code) arrive as `Object` instead of being copied.
4. `register_module` converts `members` when called, so an unconvertible
   member raises `TypeError` there rather than at import.
5. Engine values nested too deeply to convert raise `Error` of type
   `RecursionError` rather than Python's `RecursionError`.
6. Overlapping use from two threads is always detected.
7. Each operation is a message round trip and each runtime a process. On an
   Apple M-series Mac with `-O2`, a round trip (`eval("1")`) takes about
   15 µs and starting and closing a runtime about 4 ms.
8. `SPY_VERSION` is read from the bundled worker (`spy-worker --version`) on
   first access.

## 6 Alternatives considered

1. **The in-process extension.** Fastest, and what this replaces: any engine
   bug is a CPython crash.
2. **`fork` without `exec`.** Cheaper to start, but forking a threaded CPython
   is unsafe, and the child would inherit every secret of the parent's memory.
3. **WebAssembly in CPython** (as the JavaScript package does). Strong
   isolation without an OS sandbox, but it needs a WebAssembly runtime as a
   dependency and runs the engine several times slower. It remains the
   candidate for platforms without a usable OS sandbox.
4. **A pool of reusable workers.** Faster runtime creation, but a reused
   process can carry state from earlier untrusted code. A future pool must
   only hold workers that have never run code.

## 7 Tests

The suite runs against the built worker and must cover, besides the existing
API tests:

1. a worker killed by `SIGSEGV`, `SIGABRT`, and `SIGKILL` mid-operation raises
   `WorkerError` with the status, and the runtime stays lost;
2. a parent fed malformed messages by a fake worker (unknown kind or tag,
   truncated or trailing bytes, a length out of range, a count beyond the
   message, deep nesting, invalid UTF-8, non-canonical `I`, an unknown
   function id, a parent-only tag, a malformed error, an ended stream)
   terminates it and raises `WorkerError` naming the violation, without
   hanging or raising anything else; a silent fake worker times out;
3. `timeout` on `while True: pass`, and its exclusion of host-function time;
4. `memory_limit` raising a catchable `MemoryError` and the runtime working
   afterwards;
5. nested callbacks several levels deep in both directions;
6. handle release: creating and dropping many objects does not grow the
   worker's table;
7. `KeyboardInterrupt` while waiting terminates the worker;
8. the worker exits when the parent is killed;
9. the worker is sandboxed once code has run (`NoNewPrivs` and `Seccomp` in
   `/proc` on Linux, `sandbox_check` on macOS), and `mount` is refused
   afterwards.
