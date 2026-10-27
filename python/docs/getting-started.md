# Getting started

## Install

```sh
pip install small-python
# or
uv add small-python
```

The distribution is named `small-python`; the import name is `small_python`.

```python
import small_python

print(small_python.__version__)   # version of the package, e.g. 0.0.1
print(small_python.SPY_VERSION)   # version of the engine compiled into it
```

## Create a runtime

A `Runtime` owns one engine context. Use it as a context manager so the engine
is freed when you are done, or call `close()` yourself.

```python
from small_python import Runtime

with Runtime() as rt:
    print(rt.eval("sum(range(10))"))  # 45
```

## Run code: `eval` and `exec`

Both take a string of Python source and an optional `filename` used in error
messages.

- `eval(source)` runs the source and returns the value of its last expression
  statement. The source may contain any statements, not just one expression.
- `exec(source)` runs the source for its effects and returns `None`.

```python
from small_python import Runtime

with Runtime() as rt:
    rt.exec("""
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
""")
    print(rt.eval("fib(30)"))                      # 832040
    print(rt.eval("x = fib(10)\nx * 2"))           # 110
    print(rt.exec("y = 1"))                        # None
```

Globals persist between calls, so a runtime works like a long-lived module.

## Read and write globals

A runtime is subscriptable by global name.

```python
from small_python import Runtime

with Runtime() as rt:
    rt["config"] = {"retries": 3, "hosts": ["a", "b"]}
    rt.exec("count = config['retries'] * len(config['hosts'])")
    print(rt["count"])   # 6
    del rt["count"]
    print("count" in rt.eval("globals()"))  # False
```

A missing name raises `KeyError`. Plain data (`None`, `bool`, `int`, `float`,
`complex`, `str`, `bytes`, `bytearray`, `list`, `tuple`, `dict`, `set`,
`frozenset`) is copied across in both directions, so changing the copy you get
back does not change the engine's value. See
[how values convert](api.md#value-conversion).

## Call functions

`call` takes either a global name or an engine object, then positional and
keyword arguments.

```python
from small_python import Runtime

with Runtime() as rt:
    rt.exec("def greet(name, *, punctuation='!'):\n    return 'hello ' + name + punctuation")
    print(rt.call("greet", "spy"))                      # hello spy!
    print(rt.call("greet", "spy", punctuation="?"))     # hello spy?
    print(rt.call("sorted", [3, 1, 2], reverse=True))   # [3, 2, 1]

    greet = rt["greet"]          # a small_python.Object
    print(greet("world"))        # hello world!
```

## Engine objects

Values that are not plain data, such as functions, class instances,
generators, and modules, come back as `small_python.Object`. An `Object` forwards
calls, attributes, items, `len`, `in`, iteration, comparisons, hashing,
`repr`, `str`, `dir`, and truth testing to the engine.

```python
from small_python import Runtime

with Runtime() as rt:
    rt.exec("""
class Counter:
    def __init__(self):
        self.n = 0
    def bump(self, by=1):
        self.n += by
        return self.n
""")
    c = rt.call("Counter")
    c.bump()
    c.bump(by=5)
    print(c.n)                                   # 6
    c.n = 100
    print(rt.eval("[i * i for i in range(3)]"))  # [0, 1, 4]  (a list, copied)
    print(list(rt.eval("iter('abc')")))          # ['a', 'b', 'c']
```

An `Object` belongs to its runtime. Once the runtime closes, using it raises
`RuntimeError`, and passing it into a different runtime raises `ValueError`.

## Handle errors

An exception that escapes the engine is raised in Python as
`small_python.Error`.

```python
from small_python import Error, Runtime

with Runtime() as rt:
    try:
        rt.exec("x = 1\nraise ValueError('bad value')", filename="job.py")
    except Error as e:
        print(e)                  # ValueError: bad value
        print(e.type, e.message)  # ValueError bad value
        print(e.filename, e.lineno)  # job.py 2
```

Syntax errors are reported the same way, with `e.type == "SyntaxError"`.
More in the [embedding guide](embedding.md#errors).

## Next

- [Embedding guide](embedding.md) to give code access to your functions,
  modules, and files.
- [Limits and safety](safety.md) before running code you did not write.
