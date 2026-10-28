# small-python documentation

`small-python` runs Python code inside [Small Python](../README.md), a small
Python 3.15 engine written in C, from an ordinary CPython program. Each runtime
runs the engine in its own worker process, `spy-worker`, which ships inside the
package, so there is nothing else to install and nothing the engine does can
crash your program.

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

- CPython 3.10 or later.
- Linux, macOS, or Windows (x86_64). Wheels are published for all three;
  other POSIX systems build from the source distribution with a C11 compiler.
  On Windows the engine's `open()` is unavailable and the worker has no OS
  sandbox (see [Limits and safety](safety.md)).

The language itself is described in the engine manual,
[docs/manual.md](../../docs/manual.md), and the target standard in
[docs/standards/3_15.md](../../docs/standards/3_15.md).
