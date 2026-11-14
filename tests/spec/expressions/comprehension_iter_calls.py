# spec: PLS-315 13.2.6, 27.1.1
# description: a list, set or dict comprehension or a generator
# expression over an instance calls its class's Python __iter__, which may
# loop, once, in the enclosing scope and before the expression is
# evaluated further, a generator expression when it is created; the
# iterator returned, the instance itself or a generator of a generator
# function __iter__, gives the items, nested loops calling each inner
# __iter__ in turn; a value that is no iterator raises TypeError and an
# exception from __iter__ propagates, from the creation of a generator
# expression too. Inside functions as at module level.
from harness import *

log = []
class It:
    def __init__(self, n): self.n = n
    def __iter__(self):
        for _ in (): pass
        log.append("iter")
        return iter(range(self.n))
class Self:
    def __init__(self): self.i = 0
    def __iter__(self):
        for _ in (): pass
        log.append("self")
        return self
    def __next__(self):
        self.i += 1
        if self.i > 2: raise StopIteration
        return self.i
class Gen:
    def __iter__(self):
        log.append("gen")
        yield 7
class Bad:
    def __iter__(self):
        for _ in (): pass
        return 5
class Raise:
    def __iter__(self):
        for _ in (): pass
        raise LookupError("r")
def run():
    out = [[x for x in It(3)], {x for x in It(2)}, {x: 1 for x in It(2)}, list(x for x in It(2)),
           [x for x in Self()], [x for x in Gen()], [x * y for x in It(2) for y in It(2)]]
    try: [x for x in Bad()]
    except TypeError as e: out.append(str(e))
    try: (x for x in Raise())
    except LookupError as e: out.append(e.args)
    g = (x for x in It(2))
    out.append(log[:])
    out.append(list(g))
    return out

expected = [[0, 1, 2], {0, 1}, {0: 1, 1: 1}, [0, 1], [1, 2], [7], [0, 0, 0, 1],
            "Bad.__iter__() must return an iterator, not int", ("r",),
            ["iter", "iter", "iter", "iter", "self", "gen", "iter", "iter", "iter", "iter"], [0, 1]]
assert_eq(run(), expected)
log.clear()
assert_eq([x for x in It(2)] + [x for x in Self()], [0, 1, 1, 2])
assert_eq(log, ["iter", "self"])
