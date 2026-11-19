# spec: PLS-315 19.3.4
# description: zip() and map() given strict= named call each iterable's
# __iter__ in order, a Python method or a generator function, whose body
# runs only as its first item is taken; strict's truth decides whether
# unequal lengths raise ValueError naming the shorter or longer argument;
# an __iter__ that raises stops the call with its error.
from harness import *

log = []

class Gen:
    def __init__(self, tag, n): self.tag = tag; self.n = n
    def __iter__(self):
        log.append(self.tag)
        for i in range(self.n): yield (self.tag, i)

class Plain:
    def __init__(self, tag, n): self.tag = tag; self.n = n
    def __iter__(self):
        log.append(self.tag)
        return iter(range(self.n))

class Bad:
    def __iter__(self): raise KeyError("no iter")

def attempt(make):
    del log[:]
    try:
        return list(make()), list(log)
    except (ValueError, KeyError) as e:
        return type(e).__name__, str(e), list(log)

def results():
    return [
        attempt(lambda: zip(Gen("a", 2), Plain("b", 2), strict=True)),
        attempt(lambda: zip(Gen("a", 2), Plain("b", 3), strict=True)),
        attempt(lambda: zip(Gen("a", 3), Plain("b", 1), strict=1)),
        attempt(lambda: zip(Gen("a", 3), Plain("b", 1), strict=False)),
        attempt(lambda: map(lambda x, y: (x, y), Plain("b", 2), Gen("a", 3), strict=True)),
        attempt(lambda: zip(Plain("b", 1), Bad(), strict=True)),
    ]

expected = [
    ([(("a", 0), 0), (("a", 1), 1)], ["b", "a"]),
    ("ValueError", "zip() argument 2 is longer than argument 1", ["b", "a"]),
    ("ValueError", "zip() argument 2 is shorter than argument 1", ["b", "a"]),
    ([(("a", 0), 0)], ["b", "a"]),
    ("ValueError", "map() argument 2 is longer than argument 1", ["b", "a"]),
    ("KeyError", "'no iter'", ["b"]),
]

assert_eq(results(), expected)
assert_eq(results(), expected)
