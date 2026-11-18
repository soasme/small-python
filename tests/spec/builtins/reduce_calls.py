# spec: PLS-315 20.1.4, 28.7
# description: object.__reduce__, __reduce_ex__ and __getstate__, called
# as methods, unbound from object, or bound and called later, call the
# instance's Python __getstate__, __reduce__, __getnewargs__ and
# __getnewargs_ex__, which may loop; their exceptions propagate. A
# non-int protocol and a wrong argument count raise TypeError. Inside
# functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class State:
    def __init__(self): self.x = 1
    def __getstate__(self): spin(); log.append("state"); return {"x": 2}

class Args:
    def __new__(cls, *a): return object.__new__(cls)
    def __getnewargs__(self): spin(); log.append("args"); return (1, 2)

class KwArgs:
    def __new__(cls, *a, **k): return object.__new__(cls)
    def __getnewargs_ex__(self): spin(); log.append("ex"); return ((1,), {"k": 2})

class Own:
    def __reduce__(self): spin(); log.append("own"); return (Own, ())

class Bad:
    def __getstate__(self): raise KeyError("state")

class Plain:
    def __init__(self): self.y = 3

def shape(r):
    if isinstance(r, tuple): return tuple(map(shape, r))
    return r.__name__ if isinstance(r, type) or callable(r) else r

def run(f):
    del log[:]
    try:
        r = shape(f())
    except Exception as e:
        r = (type(e).__name__, str(e))
    return r, list(log)

def results():
    s, a, k, o, b = State(), Args(), KwArgs(), Own(), Bad()
    bound = s.__getstate__
    reduce_bound = a.__reduce_ex__
    return [run(lambda: s.__reduce_ex__(2)), run(lambda: object.__reduce_ex__(s, 2)), run(lambda: object.__getstate__(s)),
            run(lambda: bound()), run(lambda: reduce_bound(2)), run(lambda: a.__reduce_ex__(4)),
            run(lambda: k.__reduce_ex__(2)), run(lambda: o.__reduce_ex__(2)), run(lambda: object.__reduce_ex__(o, 2)),
            run(lambda: b.__reduce_ex__(2)), run(lambda: b.__reduce__()), run(lambda: object.__getstate__(Plain())),
            run(lambda: Plain().__reduce__()), run(lambda: s.__reduce_ex__("2")), run(lambda: s.__reduce_ex__()),
            run(lambda: s.__reduce__(1)), run(lambda: object.__getstate__())]

def main():
    return results()

expected = [(("__newobj__", ("State",), {"x": 2}, None, None), ["state"]),
            (("__newobj__", ("State",), {"x": 2}, None, None), ["state"]),
            ({"x": 1}, []), ({"x": 2}, ["state"]),
            (("__newobj__", ("Args", 1, 2), None, None, None), ["args"]),
            (("__newobj__", ("Args", 1, 2), None, None, None), ["args"]),
            (("__newobj_ex__", ("KwArgs", (1,), {"k": 2}), None, None, None), ["ex"]),
            (("Own", ()), ["own"]), (("Own", ()), ["own"]),
            (("KeyError", "'state'"), []), (("KeyError", "'state'"), []),
            ({"y": 3}, []), (("_reconstructor", ("Plain", "object", None), {"y": 3}), []),
            (("TypeError", "'str' object cannot be interpreted as an integer"), []),
            (("TypeError", "object.__reduce_ex__() takes exactly one argument (0 given)"), []),
            (("TypeError", "object.__reduce__() takes no arguments (1 given)"), []),
            (("TypeError", "unbound method object.__getstate__() needs an argument"), [])]

assert_eq(main(), expected)
assert_eq(results(), expected)
