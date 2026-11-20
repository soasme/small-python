# spec: PLS-315 27.1.6, 19.3.33, 7.5.3
# description: map() of a builtin, a builtin type or a builtin's method
# whose arguments include objects with a Python __index__, which may loop:
# each item's call converts them in order, as a direct call does, an
# __index__ error propagating from the item; in a for loop, a
# comprehension and a generator too.
from harness import *

log = []
class X:
    def __init__(self, v): self.v = v
    def __index__(self):
        for _ in (): pass
        log.append(self.v)
        if self.v == "raise": raise LookupError("x")
        return self.v

def t(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return (r, log[:])

def g():
    for x in map(round, [1.25], [X(1)]): yield x

def cases():
    return [t(lambda: list(map(round, [2.25, 3.375], [X(1), X(2)]))),
            t(lambda: list(map(int, ["11", "z"], [X(2), X(36)]))),
            t(lambda: list(map(int, ["11"], [X("raise")]))),
            t(lambda: list(map(range, [X(3)]))),
            t(lambda: list(map(range, [1, X(2)], [X(4), 5]))),
            t(lambda: list(map(str.ljust, ["a"], [X(3)]))),
            t(lambda: list(map(bytes, [X(2)]))),
            t(lambda: list(map("abc".__getitem__, [X(1), X(-1)]))),
            t(lambda: list(map(round, [2.5], ["s"]))),
            t(lambda: [x for x in map(int, ["7"], [X(10)])]),
            t(lambda: list(g()))]

expected = [([2.2, 3.38], [1, 2]), ([3, 35], [2, 36]), (("LookupError", "x"), ["raise"]),
            ([range(0, 3)], [3]), ([range(1, 4), range(2, 5)], [4, 2]), (["a  "], [3]),
            ([b"\x00\x00"], [2]), (["b", "c"], [1, -1]),
            (("TypeError", "'str' object cannot be interpreted as an integer"), []),
            ([7], [10]), ([1.2], [1])]
assert_eq(cases(), expected)
for x in map(round, [2.25], [X(1)]):
    assert_eq(x, 2.2)
