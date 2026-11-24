# spec: PLS-315 27.1.5
# description: filter() of a Python class or a callable instance calls it
# once per item as the filter reaches it, its __init__ or __call__ and the
# result's Python __bool__ each in turn, keeping the items whose result is
# true; an error from the call propagates, and the filter goes on after it.
# In a list, a for loop, a comprehension, yield from and next(), inside
# functions as at module level.
from harness import *

log = []

class Test:
    def __init__(self, n):
        for _ in (): pass
        log.append(("init", n))
        if n < 0: raise LookupError("init")
        self.n = n
    def __bool__(self):
        for _ in (): pass
        log.append(("bool", self.n))
        return self.n % 2 == 1

class Caller:
    def __call__(self, n):
        for _ in (): pass
        log.append(("call", n))
        return Test(n)

def kept():
    out = [list(filter(Test, [1, 2, 3]))]
    out.append([x for x in filter(Caller(), [3, 4])])
    for x in filter(Test, [5]): out.append(x)
    def gen():
        yield from filter(Test, [7, 8])
    out.append(list(gen()))
    f = filter(Caller(), [2, 9, 11])
    out.append((next(f), next(f)))
    return out

assert_eq(kept(), [[1, 3], [3], 5, [7], (9, 11)])
assert_eq(log, [("init", 1), ("bool", 1), ("init", 2), ("bool", 2), ("init", 3), ("bool", 3),
                ("call", 3), ("init", 3), ("bool", 3), ("call", 4), ("init", 4), ("bool", 4),
                ("init", 5), ("bool", 5), ("init", 7), ("bool", 7), ("init", 8), ("bool", 8),
                ("call", 2), ("init", 2), ("bool", 2), ("call", 9), ("init", 9), ("bool", 9),
                ("call", 11), ("init", 11), ("bool", 11)])
del log[:]
f = filter(Test, [1, -1, 3])
assert_eq(next(f), 1)
assert_raises(LookupError, next, f)
assert_eq(next(f), 3)
assert_eq(log, [("init", 1), ("bool", 1), ("init", -1), ("init", 3), ("bool", 3)])
