# spec: PLS-315 27.1.4 27.1.6 27.1.8 19.3.1
# description: Calling a subclass of zip, map, enumerate or filter that
# defines no __new__ or __init__ calls each iterable's Python __iter__ in
# order, after an enumerate's start is converted, and returns an instance
# of the subclass carrying the iterator, which gives the builtin's items
# and keeps attributes; an error of __iter__ or of the start propagates.
# A subclass's own __init__ runs after the iterators are made.
from harness import *

log = []
class It:
    def __init__(self, n): self.n = n
    def __iter__(self):
        for _ in (): pass
        log.append(("iter", self.n))
        return iter(range(self.n))

class Bad:
    def __iter__(self): raise KeyError("bad")

class E(enumerate): pass
class Z(zip): pass
class M(map): pass
class F(filter): pass
class I(enumerate):
    def __init__(self, *args):
        log.append(("init", len(args)))

def attempt(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))

def results():
    for _ in (): pass
    del log[:]
    e = E(It(2), 5)
    e.tag = "t"
    z = Z(It(1), It(2))
    out = [type(e).__name__, list(e), e.tag, type(z).__name__, isinstance(z, zip), list(z),
           list(M(abs, It(2))), list(F(None, It(3))), list(I(It(1))),
           attempt(lambda: Z(It(1), Bad(), It(3))), attempt(lambda: E(It(1), "s"))]
    return out, list(log)

expected = (["E", [(5, 0), (6, 1)], "t", "Z", True, [(0, 0)], [0, 1], [1, 2], [(0, 0)],
             ("KeyError", "'bad'"), ("TypeError", "'str' object cannot be interpreted as an integer")],
            [("iter", 2), ("iter", 1), ("iter", 2), ("iter", 2), ("iter", 3), ("iter", 1), ("init", 1),
             ("iter", 1)])

assert_eq(results(), expected)
assert_eq(results(), expected)
