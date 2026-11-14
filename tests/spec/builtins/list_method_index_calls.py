# spec: PLS-315 25.1.3, 7.5.3
# description: a list's pop() and insert() of an instance with a Python
# __index__ call it once and use the int it returns, also through a bound
# method value or starred arguments; a non-int result raises, and an
# arity error comes before any conversion; inside functions as at module
# level.
from harness import *

log = []

class X:
    def __init__(self, i): self.i = i
    def __index__(self):
        for _ in (): pass
        log.append(self.i)
        return self.i

class Real:
    def __index__(self):
        for _ in (): pass
        log.append("real")
        return 1.5

def methods():
    s = [1, 2, 3, 4]
    pop = s.pop
    a = [X(0)]
    out = [s.pop(X(1)), pop(X(-1)), s.pop(*a)]
    s.insert(X(0), 9)
    s.insert(a[0], 8)
    out.append(s)
    out.append(log[:])
    return out

assert_eq(methods(), [2, 4, 1, [8, 9, 3], [1, -1, 0, 0, 0]])
log.clear()
s = [5, 6]
assert_eq((s.pop(X(0)), s, log), (5, [6], [0]))

def errors():
    s = [1, 2]
    out = []
    for call in (lambda: s.pop(Real()), lambda: s.insert(Real(), 0), lambda: s.insert(X(0)), lambda: s.pop(X(5)),
                 lambda: [].pop(X(0))):
        log.clear()
        try: call()
        except (TypeError, IndexError) as e: out.append((type(e).__name__, str(e), log[:]))
    return out

assert_eq(errors(), [
    ("TypeError", "Real.__index__() must return an int, not float", ["real"]),
    ("TypeError", "Real.__index__() must return an int, not float", ["real"]),
    ("TypeError", "insert expected 2 arguments, got 1", []),
    ("IndexError", "pop index out of range", [5]),
    ("IndexError", "pop from empty list", [0]),
])
