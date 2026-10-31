# API reference

```python
import small_python
from small_python import Runtime, Object, Error, WorkerError, Timeout, SPY_VERSION
```

## `Runtime`

```python
Runtime(*, std=True, step_limit=0, memory_limit=0, timeout=None,
        output=None, loader=None, message_limit=64 << 20)
```

An independent engine context with its own globals and modules, running in
its own worker process. Creating one starts the worker; `WorkerError` if it
cannot start.

| Argument | Meaning |
|---|---|
| `std` | Register the standard modules (`sys` and `gc`). |
| `step_limit` | Maximum evaluation steps, counted from the start of each `eval` or `exec`; `0` is unlimited. Exceeding it raises `RuntimeError` in the engine. Must be `>= 0`. |
| `memory_limit` | Bytes the engine may hold allocated; `0` is unlimited. Exceeding it stops the operation with `MemoryError`, which code cannot catch; the runtime keeps working. |
| `timeout` | Seconds one operation may run in the worker, or `None`. Time spent in host functions, `output`, and `loader` does not count. Exceeding it stops the operation and raises `Timeout`; the runtime stays open. |
| `output` | Callable receiving each piece of printed text; `None` writes to `sys.stdout`. |
| `loader` | Callable mapping a module name to its source `str`, or `None` when there is no such module. |
| `message_limit` | Largest message between the runtime and its worker, in bytes. A value too large to send raises `ValueError` (from Python) or `OverflowError` (in the engine). |

### Running code

- `eval(source, filename="<string>")`: Run `source` and return the value of its last expression statement (or
  `None`).
- `exec(source, filename="<string>")`: Run `source` for its effects; returns `None`.
- `call(function, /, *args, **kwargs)`: Call `function`, which is a global name (`str`) or an `Object`, and return
  the converted result.

### Globals

- `rt[name]`: The global `name`, converted. `KeyError` if it is not defined.
- `rt[name] = value`: Set a global. `TypeError` if `value` cannot be converted.
- `del rt[name]`: Delete a global. `KeyError` if it is not defined.

### Extending the engine

- `define(name, function)`: Bind a Python callable as the global `name`.
- `function(func=None, *, name=None)`: Decorator form of `define`; the global is named `name` or `func.__name__`.
  Returns `func`.
- `register_module(name, members=None, source=None)`: Make `import name` produce a module whose attributes are `members` (a dict
  with `str` keys), after which `source` (a `str`) runs in the module's
  namespace. Built on first import.
- `mount(directory, path=None, *, read_only=False)`: Let the engine's `open()` reach host `directory` at the absolute engine path
  `path` (default: the directory's resolved path). Raises `Error` if the
  directory does not exist, and `Error` of type `PermissionError` once code
  has run in the runtime (the worker is then sandboxed to the mounts it has).

### Lifetime

- `collect()`: Run the cycle collector; returns the number of values freed.
- `close()`: End the worker. Every `Object` from this runtime stops working.
  Calling it again does nothing.
- `closed`: `True` after `close()`, or once the worker is lost.
- `version`: The engine version reported by the worker.

A runtime is a context manager; leaving the `with` block calls `close()`.
Closing also drops the runtime's references to host functions, module
members, `output`, and `loader`. Methods of a closed runtime raise
`RuntimeError`. `eval`, `exec`, and `close` raise `RuntimeError` when called
from a host function, `output`, or `loader` of the same runtime.

While a host function, `output`, or `loader` runs, the runtime belongs to the
thread running it: using the runtime or its objects from another thread raises
`RuntimeError`.

`rt[name]` looks a name up the way engine code does, in globals and then
builtins, so `rt["len"]` is the builtin `len`. Assigning and deleting change
globals only.

## `Object`

An engine value that is not converted to a Python value. It supports:

| Python operation | Engine operation |
|---|---|
| `obj(*args, **kwargs)` | call |
| `obj.name`, `obj.name = v` | attribute get and set |
| `obj[key]`, `obj[key] = v` | item get and set |
| `len(obj)`, `x in obj` | `len`, `in` |
| `iter(obj)`, `next(obj)` | iteration |
| `==`, `!=`, `<`, `<=`, `>`, `>=` | the same comparison |
| `hash(obj)` | `hash` |
| `repr(obj)`, `str(obj)`, `dir(obj)` | `repr`, `str`, `dir` |
| `bool(obj)` | truth value |

Every attribute comes from the engine value, including `__doc__`,
`__class__`, and `__dict__`; Python's own attributes of the wrapper are used
only for names the engine value lacks. Comparing with a Python value that
cannot be converted is not equal (`==` is `False`) and ordering raises
`TypeError`. Objects from different runtimes are never equal.

These operations raise the Python exception a protocol expects: a missing
attribute raises `AttributeError`, a missing key `KeyError` (with the key),
an index out of range `IndexError`, and an unsupported operation (`len` of a
value without one, hashing a list, `next` on a non-iterator) `TypeError`.
Other engine exceptions, and any exception from a call, raise `Error`.

Deleting attributes or items is not supported (`TypeError`). After the runtime
closes, every operation except `repr` raises `RuntimeError`.

## `WorkerError` and `Timeout`

`WorkerError` (a `RuntimeError`) means the worker is gone: it crashed, it sent
something the protocol does not allow, or it was terminated. `returncode` is
its exit status (negative for a signal), or `None`. The runtime is then
closed; every later operation, including those of its `Object`s, raises
`WorkerError` again. Its state is lost: make a new `Runtime`.

`Timeout` (a `WorkerError` and a `TimeoutError`) means an operation ran past
`timeout`. The engine stops it and the runtime stays open; only a worker that
does not stop within a further second is terminated, which closes the
runtime.

A `KeyboardInterrupt` that arrives while the runtime waits for its worker
terminates the worker and propagates.

## `Error`

Subclass of `Exception` raised when an exception escapes the engine.

| Attribute | Meaning |
|---|---|
| `type` | Engine exception class name, qualified by its module unless it is a builtin |
| `message` | Engine exception message |
| `exception` | The engine exception as an `Object` |
| `filename` | File name given to `eval`/`exec` |
| `lineno` | Line number |

`str(error)` is `"type: message"`, or `type` alone when there is no message.
`filename` and `lineno` are `None` on an `Error` made directly.

When the escaping exception came from a host function (or the loader) and
engine code did not handle it, the original Python exception is the `Error`'s
`__cause__`. If that original is a `KeyboardInterrupt`, `SystemExit`, or other
`BaseException` that is not an `Exception`, it is re-raised itself instead of
an `Error`.

## Value conversion

Values are converted whenever they cross between Python and the engine:
arguments, return values, globals, module members, and exception arguments.

| Python | Engine | Notes |
|---|---|---|
| `None`, `bool` | same | |
| `int` | `int` | any size |
| `float`, `complex` | same | |
| `str`, `bytes`, `bytearray` | same | copied |
| `list`, `tuple`, `dict`, `set`, `frozenset` | same | copied recursively; at most 200 levels deep (`RecursionError`) |
| callable | native function | keeps a reference to the callable; receives positional and keyword arguments |
| `Object` | the wrapped value | must belong to the same runtime, else `ValueError` |
| anything else | | `TypeError` |

Python subclasses of these types convert as their base type. From the
engine, values whose type is exactly one of the first five rows come back as
the same Python type; every other value (functions, classes, instances,
iterators, modules, and instances of subclasses such as a `dict` subclass)
comes back as an `Object`. An engine value nested more than 200 levels deep
raises `Error` of type `RecursionError`. A Python callable passed in and read back
returns as an `Object` wrapping the native function, not the original
callable.

## Module constants

- `SPY_VERSION`: Version of the engine bundled with the package.
- `__version__`: Version of the `small-python` distribution.

The package ships type information (`py.typed` and `_runtime.pyi`).
