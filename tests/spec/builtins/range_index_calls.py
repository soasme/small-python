# spec: PLS-315 25.3.1, 7.5.3
# description: range() of instances with a Python __index__ calls each
# once, in argument order, and builds the range of the ints they return,
# also through starred arguments; an argument that is neither an int nor
# such an instance, or a non-int result, raises before the later
# arguments are converted; an int's subclass is its int; inside functions
# as at module level.
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

class I(int):
    def __index__(self):
        log.append("own")
        return 0

def ranges():
    a = [X(1), X(9), X(3)]
    out = [list(range(X(3))), list(range(X(1), 4)), list(range(0, X(9), X(3))), range(*a), range(a[0], a[1]),
           range(X(1 << 70))[-1] == (1 << 70) - 1, list(range(I(2)))]
    out.append(log[:])
    return out

assert_eq(ranges(), [[0, 1, 2], [1, 2, 3], [0, 3, 6], range(1, 9, 3), range(1, 9), True, [0, 1],
                     [3, 1, 9, 3, 1, 9, 3, 1, 9, 1 << 70]])
log.clear()
assert_eq((range(X(2), X(4)), log), (range(2, 4), [2, 4]))

def errors():
    out = []
    for args in ((X(1), "a", X(2)), ("a", X(1)), (X(1), Real(), X(2)), (X(0), X(5), X(0))):
        log.clear()
        try: range(*args)
        except (TypeError, ValueError) as e: out.append((type(e).__name__, str(e), log[:]))
    return out

assert_eq(errors(), [
    ("TypeError", "'str' object cannot be interpreted as an integer", [1]),
    ("TypeError", "'str' object cannot be interpreted as an integer", []),
    ("TypeError", "Real.__index__() must return an int, not float", [1, "real"]),
    ("ValueError", "range() arg 3 must not be zero", [0, 5, 0]),
])
