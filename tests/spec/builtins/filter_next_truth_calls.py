# spec: PLS-315 27.1.8 27.1.4 6.11
# description: next() of a filter whose function is None, bool or another
# builtin tests each item as the filter's iteration does, an instance's
# Python __bool__, __len__ or conversion method called in order, until
# one is kept; next()'s default is returned at the end, and an error of
# the test propagates, the filter going on from the next item after it.
from harness import *

log = []
class T:
    def __init__(self, v): self.v = v
    def __bool__(self):
        for _ in (): pass
        log.append(("bool", self.v))
        if self.v < 0: raise LookupError("bool")
        return self.v > 0

class L:
    def __init__(self, n): self.n = n
    def __len__(self):
        for _ in (): pass
        log.append(("len", self.n))
        return self.n

class N:
    def __init__(self, v): self.v = v
    def __index__(self):
        log.append(("index", self.v))
        return self.v
    def __int__(self):
        log.append(("int", self.v))
        return self.v

def attempt(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))

def results():
    for _ in (): pass
    del log[:]
    truth = filter(None, [0, T(0), T(-1), T(2), L(1)])
    by_bool = filter(bool, [L(0), L(3)])
    by_int = filter(int, [N(0), N(4)])
    out = [attempt(lambda: next(truth)), next(truth).v, next(truth).n, next(truth, "end"),
           next(by_bool).n, next(by_bool, "end"), next(by_int).v, next(filter(None, range(3)))]
    return out, list(log)

expected = ([("LookupError", "bool"), 2, 1, "end", 3, "end", 4, 1],
            [("bool", 0), ("bool", -1), ("bool", 2), ("len", 1), ("len", 0), ("len", 3),
             ("int", 0), ("int", 4)])

assert_eq(results(), expected)
assert_eq(results(), expected)
