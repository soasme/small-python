# spec: PLS-315 20.1.3
# description: The first object.__reduce_ex__ a program calls, before any
# other reduction, here inside a function, gives what later ones give,
# inside a generator, at module level, or from __reduce__ and
# __getstate__: a Python __getstate__ it calls may loop, and its exception
# propagates.
from harness import *

log = []

class Point:
    def __init__(self, x): self.x = x
    def __getstate__(self):
        for _ in range(2): pass
        log.append("state")
        if self.x == "bad": raise LookupError("state")
        return {"x": self.x}

def reduced(p):
    r = p.__reduce_ex__(2)
    return r[0].__name__, r[1][0] is Point, r[2]

def first():
    return reduced(Point(1))

def gen():
    yield reduced(Point(2))

assert_eq(first(), ("__newobj__", True, {"x": 1}))
assert_eq(next(gen()), ("__newobj__", True, {"x": 2}))
assert_eq(reduced(Point(3)), ("__newobj__", True, {"x": 3}))
try:
    reduced(Point("bad"))
except LookupError as e:
    assert_eq(str(e), "state")
assert_eq(log, ["state"] * 4)
assert_eq(object.__getstate__(Point(4)), {"x": 4})
assert_eq(Point(5).__reduce__()[0].__name__, "_reconstructor")
