# spec: PLS-315 27.1.3, 13.10
# description: a callable iterator iter(f, sentinel) compares each result
# of f with the sentinel by sentinel == result: the sentinel's Python
# __eq__, which may loop, first, unless the result's class is a subclass
# of the sentinel's, whose reflected __eq__ comes first, or the
# sentinel's own comparison is native; a NotImplemented leaves the other
# method and then identity. A true comparison ends the iterator, an
# error from __eq__ propagates. For loops, comprehensions, consumers and
# next(), inside functions as at module level.
from harness import *

log = []

class S:
    def __init__(self, n): self.n = n
    def __eq__(self, other):
        for _ in (): pass
        log.append(("eq", self.n, getattr(other, "n", other)))
        if other is -1: raise KeyError("eq")
        if other is -2: return NotImplemented
        return getattr(other, "n", other) == self.n

class T(S):
    def __eq__(self, other):
        for _ in (): pass
        log.append(("teq", self.n, getattr(other, "n", other)))
        return NotImplemented

def counter(xs):
    it = iter(xs)
    return lambda: next(it)

def compares():
    out = [list(iter(counter([1, 2, 3, 4]), S(3)))]
    for x in iter(counter([5, 6, 7]), S(6)): out.append(x)
    it = iter(counter([T(1), T(2)]), S(2))
    out.append((next(it).n, [x for x in it]))
    try: list(iter(counter([0, -1, 2]), S(9)))
    except KeyError as e: out.append(e.args)
    out.append(list(iter(counter([-2, 4]), S(4))))
    out.append(list(iter(counter([2, S(1), 3]), 1)))
    out.append(sum(iter(counter([1, 2, 3, 4]), S(4))))
    return out

expected = [[1, 2], 5, (1, []), ("eq",), [-2], [2], 6]
expected_log = [("eq", 3, 1), ("eq", 3, 2), ("eq", 3, 3), ("eq", 6, 5), ("eq", 6, 6),
                ("teq", 1, 2), ("eq", 2, 1), ("teq", 2, 2), ("eq", 2, 2), ("eq", 9, 0), ("eq", 9, -1),
                ("eq", 4, -2), ("eq", 4, 4), ("eq", 1, 1), ("eq", 4, 1), ("eq", 4, 2), ("eq", 4, 3), ("eq", 4, 4)]
assert_eq(compares(), expected)
assert_eq(log, expected_log)
log.clear()

assert_eq([x for x in iter(counter([7, 8]), S(8))], [7])
assert_eq(log, [("eq", 8, 7), ("eq", 8, 8)])
