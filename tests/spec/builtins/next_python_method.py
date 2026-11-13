# spec: PLS-315 19.3.27
# description: next() of an instance calls its class's Python __next__,
# which may call others or not, and returns its value; with a default, a StopIteration
# from it gives the default while any other exception, or one without a
# default, propagates; a class without __next__ raises TypeError, an
# instance's own __next__ entry is not looked up, and map(next, ...) calls
# each item's; inside functions as at module level.
from harness import *

log = []

class Counter:
    def __init__(self, n): self.n = n
    def __next__(self):
        log.append(self.n)
        if self.n == 0: raise StopIteration("done")
        if self.n < 0: raise KeyError("k")
        self.n -= 1
        return self.n

class Quick(Counter):
    def __next__(self):
        # No call: the method runs as an expression.
        if self.n == 0: raise StopIteration
        if self.n < 0: raise KeyError
        self.n -= 1
        return self.n

class Plain: pass

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def calls():
    del log[:]
    c = Counter(2)
    out = [next(c), next(c, "d"), next(c, "d"), next(Counter(0), None), next(Counter(1), ())]
    out.append(error(lambda: next(Counter(0))))
    out.append(error(lambda: next(Counter(-1), 0)))
    out.append(error(lambda: next(Plain(), 0)))
    own = Plain()
    own.__next__ = lambda: 1
    out.append(error(lambda: next(own)))
    out.append(list(map(next, [Counter(3), Counter(1)])))
    q = Quick(1)
    out.append([next(q), next(q, "e"), error(lambda: next(q)), error(lambda: next(Quick(-1), 0))])
    out.append(list(log))
    return out

expected = [1, 0, "d", None, 0, ("StopIteration", "done"), ("KeyError", "'k'"),
            ("TypeError", "'Plain' object is not an iterator"), ("TypeError", "'Plain' object is not an iterator"),
            [2, 0], [0, "e", ("StopIteration", ""), ("KeyError", "")],
            [2, 1, 0, 0, 1, 0, -1, 3, 1]]
assert_eq(calls(), expected)
assert_eq(calls(), expected)
c = Counter(1)
log.clear()
assert_eq([next(c), next(c, 5), next(Counter(0), 6)], [0, 5, 6])
assert_eq(log, [1, 0, 0])
