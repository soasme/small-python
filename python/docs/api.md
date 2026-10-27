# API reference

```python
import small_python
from small_python import Runtime, Object, Error, SPY_VERSION
```

## `Runtime`

```python
Runtime(*, std=True, step_limit=0, output=None, loader=None)
```

An independent engine context with its own globals and modules.

| Argument | Meaning |
|---|---|
| `std` | Register the standard modules (`sys`, `gc`, `weakref`, `collections`, `itertools`, `types`, `_thread`, `_typing`). |
| `step_limit` | Maximum evaluation steps, counted from the start of each `eval` or `exec`; `0` is unlimited. Exceeding it raises `RuntimeError` in the engine. Must be `>= 0`. |
| `output` | Callable receiving each piece of printed text; `None` writes to `sys.stdout`. |
| `loader` | Callable mapping a module name to its source `str`, or `None` when there is no such module. |

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
  directory does not exist.

### Lifetime

- `collect()`: Run the cycle collector; returns the number of values freed.
- `close()`: Free the engine context. Every `Object` from this runtime stops working.
  Calling it again does nothing.
- `closed`: `True` after `close()`.

A runtime is a context manager; leaving the `with` block calls `close()`.
Methods of a closed runtime raise `RuntimeError`. `eval`, `exec`, and `close`
raise `RuntimeError` when called from a host function of the same runtime.

## `Object`

An engine value that is not converted to a Python value. It supports:

| Python operation | Engine operation |
|---|---|
| `obj(*args, **kwargs)` | call |
| `obj.name`, `obj.name = v` | attribute get and set |
| `obj[key]`, `obj[key] = v` | item get and set |
| `iter(obj)`, `next(obj)` | iteration |
| `repr(obj)`, `str(obj)` | `repr` and `str` |
| `bool(obj)` | truth value |

Deleting attributes or items is not supported (`TypeError`). `obj.runtime` is
the owning `Runtime`. After the runtime closes, every operation except `repr`
raises `RuntimeError`.

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

## Value conversion

Values are converted whenever they cross between Python and the engine:
arguments, return values, globals, module members, and exception arguments.

| Python | Engine | Notes |
|---|---|---|
| `None`, `bool` | same | |
| `int` | `int` | any size |
| `float`, `complex` | same | |
| `str`, `bytes`, `bytearray` | same | copied |
| `list`, `tuple`, `dict`, `set`, `frozenset` | same | copied recursively; at most 200 levels deep |
| callable | native function | keeps a reference to the callable; receives positional and keyword arguments |
| `Object` | the wrapped value | must belong to the same runtime, else `ValueError` |
| anything else | | `TypeError` |

From the engine, the types in the first five rows come back as the same Python
type; every other value (functions, classes, instances, iterators, modules,
...) comes back as an `Object`. A Python callable passed in and read back
returns as an `Object` wrapping the native function, not the original
callable.

## Module constants

- `SPY_VERSION`: Version of the engine compiled into the package.
- `__version__`: Version of the `small-python` distribution.
