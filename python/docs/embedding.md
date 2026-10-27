# Embedding guide

Code in a runtime can only use what the host gives it. This page covers the
ways to give it something: functions, modules, an import loader, an output
sink, and directories.

## Host functions

`define(name, function)` binds any Python callable as a global in the engine.
The `function` decorator does the same and returns the function unchanged.

```python
from small_python import Runtime

with Runtime() as rt:
    @rt.function
    def add(a, b=10, *, scale=1):
        return (a + b) * scale

    @rt.function(name="shout")
    def upper(text):
        return text.upper()

    rt.define("now", lambda: "2026-10-27")

    print(rt.eval("add(1)"))               # 11
    print(rt.eval("add(1, 2, scale=3)"))   # 9
    print(rt.eval("shout('hi')"))          # HI
    print(rt.eval("add.__name__"))         # add
```

Arguments are converted to Python values on the way in and the return value is
converted back on the way out ([conversion rules](api.md#value-conversion)).
Engine functions, instances, and other objects arrive as `small_python.Object`,
so a host function can call back into code it is given:

```python
from small_python import Runtime

with Runtime() as rt:
    rt.define("apply", lambda f, n: f(n))
    rt.exec("def square(n): return n * n")
    print(rt.eval("apply(square, 7)"))         # 49
    print(rt.eval("apply(lambda n: -n, 7)"))   # -7
```

A host function must not call `eval`, `exec`, or `close` on the runtime that
is calling it; those raise `RuntimeError`, which reaches the engine as a
`RuntimeError`.

The runtime keeps a reference to each callable until it closes.

### Exceptions from host functions

A Python exception raised by a host function becomes an engine exception, so
engine code can catch it. The engine class is the builtin exception whose name
matches the nearest class in the Python exception's MRO, falling back to
`RuntimeError`, and it gets the same `args`.

```python
from small_python import Runtime

with Runtime() as rt:
    @rt.function
    def fetch(key):
        raise KeyError(key)

    rt.exec("""
try:
    fetch('missing')
except LookupError as e:
    caught = repr(e)
""")
    print(rt["caught"])   # KeyError('missing')
```

A custom subclass such as `class NotFound(KeyError)` arrives as `KeyError`.
If a host function lets a `small_python.Error` escape (for example, from
calling an engine function that raised), the original engine exception is
re-raised unchanged.

## Modules

`register_module(name, members=None, source=None)` makes `import name` work in
the engine. `members` is a dict of attribute names to values (functions,
constants, or plain data); `source` is Python code run in the module's
namespace after the members are set, so it can use them. The module is built on
its first import.

```python
from small_python import Runtime

def http_get(url):
    return f"<html for {url}>"

with Runtime() as rt:
    rt.register_module(
        "web",
        {"get": http_get, "TIMEOUT": 30},
        source="""
def title(url):
    return get(url).upper()
""",
    )
    rt.exec("import web")
    print(rt.eval("web.TIMEOUT"))           # 30
    print(rt.eval("web.title('a.com')"))    # <HTML FOR A.COM>
    rt.exec("from web import get")
    print(rt.eval("get('b.com')"))          # <html for b.com>
```

Registered modules are found before the loader.

### Loading modules on demand

`Runtime(loader=...)` installs a function called with a module name when code
imports something that is not registered or built in. Return the module's
source as a `str`, or `None` if there is no such module.

```python
from small_python import Error, Runtime

sources = {
    "greeting": "WORD = 'hi'",
    "shapes": "def area(w, h): return w * h",
}

with Runtime(loader=sources.get) as rt:
    rt.exec("import greeting, shapes")
    print(rt.eval("shapes.area(2, 3)"))   # 6
    try:
        rt.exec("import nowhere")
    except Error as e:
        print(e.type)                     # ModuleNotFoundError
```

Without a loader, importing anything else raises `ModuleNotFoundError`.

### Standard modules

`Runtime(std=True)` (the default) registers the engine's standard modules:
`sys`, `gc`, `weakref`, `collections`, `itertools`, `types`, `_thread`, and
`_typing`. Pass `std=False` for a runtime with only builtins. Other library
modules (`json`, `re`, `math`, ...) are not part of the engine; provide them
with `register_module` or a loader if code needs them.

## Printed output

`print` writes to `sys.stdout` of the host process by default. Pass
`output=` to receive the text instead; it is called with each piece of text
as it is printed.

```python
from small_python import Runtime

chunks = []
with Runtime(output=chunks.append) as rt:
    rt.exec("print('total:', 3)\nprint('done', end='')")
print(repr("".join(chunks)))   # 'total: 3\ndone'
```

`input()` in the engine raises `EOFError`; to read input, give code a host
function instead.

## Files

The engine's `open()` reaches no files until you mount a host directory with
`mount(directory, path=None, *, read_only=False)`. `path` is the absolute
path the directory appears at inside the engine; by default it is the
directory's own resolved path. Relative paths in the engine start at the first
mount.

```python
import tempfile
from small_python import Error, Runtime

with tempfile.TemporaryDirectory() as work, Runtime() as rt:
    rt.mount(work, "/work")
    rt.exec("with open('/work/out.txt', 'w') as f:\n    f.write('hello')")
    print(open(f"{work}/out.txt").read())          # hello
    print(rt.eval("open('out.txt').read()"))       # hello (relative to /work)

    rt.mount(work, "/data", read_only=True)
    try:
        rt.exec("open('/data/new.txt', 'w')")
    except Error as e:
        print(e.type)                              # OSError
```

Paths are checked so that `..` and symbolic links cannot leave a mount. Files
not under a mount raise `PermissionError`.

## Errors

`small_python.Error` carries:

| Attribute | Meaning |
|---|---|
| `type` | Name of the engine exception class: `"ZeroDivisionError"` for a builtin, `"__main__.QuotaExceeded"` for one defined in code |
| `message` | The exception's message (`str(exc)` in the engine) |
| `exception` | The engine exception itself, as a `small_python.Object` |
| `filename` | The `filename` passed to `eval`/`exec` (default `"<string>"`) |
| `lineno` | Line where it was raised |

`str(error)` is `"Type: message"`. Use `exception` to read engine-side
details:

```python
from small_python import Error, Runtime

with Runtime() as rt:
    rt.exec("class QuotaExceeded(Exception):\n    def __init__(self, used):\n"
            "        super().__init__('over quota')\n        self.used = used")
    try:
        rt.exec("raise QuotaExceeded(120)")
    except Error as e:
        print(e.type, e.exception.used)   # __main__.QuotaExceeded 120
```

Errors raised by the binding itself are ordinary Python exceptions: `TypeError`
for a value that cannot be converted, `KeyError` for a missing global,
`ValueError` for an object from another runtime, and `RuntimeError` for a
closed runtime.

## Garbage collection

The engine frees most values by reference counting. `collect()` runs its cycle
collector and returns the number of values freed; call it at convenient points
in a long-lived runtime that creates reference cycles. `close()` frees
everything, cycles included.
