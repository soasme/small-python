# small-python documentation

`small-python` runs Python code inside [Small Python](../README.md), a small
Python 3.15 engine written in C, from an ordinary CPython program. The engine
is compiled into the package's extension module `small_python._core`, so there
is nothing else to install.

Each `small_python.Runtime` is a separate interpreter with its own globals and
modules. The code it runs sees only what you hand it: builtins, the few
standard modules you allow, functions you define for it, and directories you
mount. It cannot import modules from your CPython environment.

```python
import small_python

with small_python.Runtime() as rt:
    @rt.function
    def lookup(key):
        return {"answer": 42}.get(key)

    print(rt.eval("lookup('answer') * 2"))  # 84
```

## Contents

1. [Getting started](getting-started.md): install, run code, read and write
   globals, call functions, close a runtime.
2. [Embedding guide](embedding.md): host functions, modules, imports, printed
   output, files, and errors.
3. [Limits and safety](safety.md): bounding execution and what a runtime can
   and cannot reach.
4. [API reference](api.md): `Runtime`, `Object`, `Error`, and how values
   convert.
5. [Development](development.md): build from source, run the tests, release.

## Requirements

- CPython 3.13 or later.
- Linux or macOS. Wheels are published for both; other POSIX systems build
  from the source distribution with a C11 compiler. Windows is not supported.

The language itself is described in the engine manual,
[docs/smallpython.md](../../docs/smallpython.md), and the target standard in
[docs/standards/3_15.md](../../docs/standards/3_15.md).
