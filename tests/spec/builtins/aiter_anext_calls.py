# spec: PLS-315 19.3.2, 19.3.4
# description: aiter() and anext() call an object's Python __aiter__ and
# __anext__, which may loop, or read them through a descriptor's Python
# __get__ first; aiter() checks what __aiter__ returns has __anext__, and
# anext() with a default wraps the awaitable __anext__ returns; errors
# from either method, or from __get__, propagate; called directly,
# starred, inside functions and generators, as at module level.
from harness import *

log = []

class Step:
    def __init__(self, n): self.n = n
    def __await__(self):
        for _ in range(1): pass
        if self.n is None: raise StopAsyncIteration
        return self.n
        yield

class Items:
    def __init__(self, *items): self.items = list(items)
    def __aiter__(self):
        for _ in range(2): pass
        log.append("aiter")
        return self
    def __anext__(self):
        for _ in range(2): pass
        log.append("anext")
        return Step(self.items.pop(0) if self.items else None)

class Getter:
    def __init__(self, name): self.name = name
    def __get__(self, obj, cls):
        for _ in range(1): pass
        log.append(("get", self.name, type(obj).__name__, cls.__name__))
        if self.name == "missing": raise LookupError(self.name)
        return lambda: obj if self.name == "__aiter__" else Step(7)

class Read:
    __aiter__ = Getter("__aiter__")
    __anext__ = Getter("__anext__")

class Missing:
    __anext__ = Getter("missing")

class Plain:
    def __aiter__(self):
        for _ in range(1): pass
        return 1

class Failing:
    def __anext__(self):
        for _ in range(1): pass
        raise LookupError("anext")

def drive(aw):
    it = aw.__await__()
    try:
        it.send(None)
    except StopIteration as e:
        return e.value
    raise AssertionError("suspended")

def run(f, *args):
    for _ in range(1): pass
    del log[:]
    try: r = f(*args)
    except Exception as e: r = (type(e).__name__, str(e))
    if isinstance(r, Step): r = ("step", r.n)
    elif type(r).__name__ == "anext_awaitable": r = ("awaitable", drive(r))
    elif not isinstance(r, (int, tuple)): r = type(r).__name__
    return r, log[:]

def cases():
    it = Items(1)
    return [run(aiter, it), run(anext, it), run(anext, Items(), "end"), run(anext, Items(5), "end"),
            run(aiter, Read()), run(anext, Read()), run(anext, Missing()), run(anext, Missing(), 0),
            run(aiter, Plain()), run(anext, Failing()), run(anext, Failing(), 0), run(aiter, 1), run(anext, 1)]

expected = [
    ("Items", ["aiter"]), (("step", 1), ["anext"]), (("awaitable", "end"), ["anext"]), (("awaitable", 5), ["anext"]),
    ("Read", [("get", "__aiter__", "Read", "Read")]), (("step", 7), [("get", "__anext__", "Read", "Read")]),
    (("LookupError", "missing"), [("get", "missing", "Missing", "Missing")]),
    (("LookupError", "missing"), [("get", "missing", "Missing", "Missing")]),
    (("TypeError", "Plain.__aiter__() must return an async iterator, not int"), []),
    (("LookupError", "anext"), []), (("LookupError", "anext"), []),
    (("TypeError", "'int' object is not an async iterable"), []),
    (("TypeError", "'int' object is not an async iterator"), []),
]

def starred(f, *args):
    for _ in range(1): pass
    return f(*args)

def through(f, *args):
    return run(starred, f, *args)

def gen():
    for case in cases():
        yield case

assert_eq(cases(), expected)
it = Items(1)
assert_eq([run(aiter, it), run(anext, it), run(anext, Read()), run(aiter, Plain())], [expected[0], expected[1], expected[5], expected[8]])
assert_eq([through(aiter, Read()), through(anext, Items(), "end"), through(anext, Failing())], [expected[4], expected[2], expected[9]])
assert_eq(list(gen()), expected)
