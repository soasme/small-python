# spec: PLS-315 27.1.8 27.1.4 7.7.4
# description: filter() takes each item of an iterator that gives it by a
# call, a __getitem__ iterator, iter(f, sentinel), a map or an enumerate
# of one, as that iterator gives it, then tests it by its function or its
# truth, in order: a __getitem__'s IndexError or the sentinel ends the
# filter, and an error of the call propagates.
from harness import *

log = []
class Seq:
    def __getitem__(self, i):
        for _ in (): pass
        log.append(("item", i))
        if i >= 4: raise IndexError(i)
        return i % 2

def counter():
    n = [0]
    def step():
        for _ in (): pass
        n[0] += 1
        log.append(("step", n[0]))
        return n[0]
    return step

def less(x):
    for _ in (): pass
    log.append(("less", x))
    return x - 1

def bad(x): raise KeyError(x)

class Truth:
    def __init__(self, v): self.v = v
    def __bool__(self):
        log.append(("bool", self.v))
        return self.v > 1

def attempt(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))

def results():
    for _ in (): pass
    del log[:]
    out = [list(filter(None, Seq())), list(filter(lambda x: x == 0, Seq())), list(filter(None, iter(counter(), 3))),
           list(filter(None, map(less, [1, 2]))), list(filter(bool, enumerate(map(less, [1])))),
           [t.v for t in filter(None, map(Truth, [1, 2]))],
           attempt(lambda: list(filter(None, map(bad, [1]))))]
    return out, list(log)

expected = ([[1, 1], [0, 0], [1, 2], [1], [(0, 0)], [2], ("KeyError", "1")],
            [("item", 0), ("item", 1), ("item", 2), ("item", 3), ("item", 4),
             ("item", 0), ("item", 1), ("item", 2), ("item", 3), ("item", 4),
             ("step", 1), ("step", 2), ("step", 3), ("less", 1), ("less", 2), ("less", 1),
             ("bool", 1), ("bool", 2)])

assert_eq(results(), expected)
assert_eq(results(), expected)
