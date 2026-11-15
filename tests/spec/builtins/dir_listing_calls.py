# spec: PLS-315 19.3.12, 7.5.3
# description: dir() of an instance whose Python __dir__ is a generator
# function, or returns a generator, an iterator or an instance with a
# Python __iter__, each of which may loop, lists the items in order, then
# sorts them as sorted() does, calling items' Python __lt__; an error the
# generator raises propagates and a non-iterable raises TypeError. Inside
# functions as at module level.
from harness import *

log = []

class Gen:
    def __dir__(self):
        for _ in range(2): pass
        log.append("dir")
        yield "b"; log.append("b")
        yield "a"; log.append("a")
        yield "c"

class Items:
    def __iter__(self):
        for _ in range(2): pass
        log.append("iter")
        return iter(["y", "x"])

class Returns:
    def __dir__(self): return Items()

class Name:
    def __init__(self, n): self.n = n
    def __lt__(self, other):
        for _ in range(2): pass
        log.append(("lt", self.n, other.n))
        return self.n < other.n
    def __repr__(self): return self.n

class Named:
    def __dir__(self): return (Name(n) for n in "ba")

class Raises:
    def __dir__(self):
        yield "a"
        raise LookupError("dir")

class Bad:
    def __dir__(self): return 5

def listings():
    out = [dir(Gen()), dir(Returns()), [n.n for n in dir(Named())], dir(type("K", (), {"__dir__": lambda self: iter("qp")})())]
    for o in (Raises(), Bad()):
        try: dir(o)
        except LookupError as e: out.append(e.args)
        except TypeError as e: out.append(str(e))
    return out

expected = [["a", "b", "c"], ["x", "y"], ["a", "b"], ["p", "q"], ("dir",), "'int' object is not iterable"]
assert_eq(listings(), expected)
assert_eq(log, ["dir", "b", "a", "iter", ("lt", "a", "b")])
log.clear()
assert_eq(dir(Gen()), ["a", "b", "c"])
assert_eq(log, ["dir", "b", "a"])
