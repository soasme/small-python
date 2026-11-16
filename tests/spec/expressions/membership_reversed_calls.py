# spec: PLS-315 13.10, 27.1.7, 7.2.5
# description: in and not in of a reversed list or tuple iterator compare
# its remaining items, last first, with x by RichCompareBool, an item's
# Python __eq__ or x's, which may loop, first and an identical item
# matching without a call; the search stops past the match, leaving the
# iterator at the items before it. Items with no Python __eq__ compare
# without a call. Inside functions and comprehensions as
# at module level.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class K:
    def __init__(self, n): self.n = n
    def __eq__(self, other):
        spin(); log.append((self.n, getattr(other, "n", other)))
        return self.n == getattr(other, "n", other)
    __hash__ = object.__hash__
    def __repr__(self): return "K%d" % self.n

def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def main():
    it = reversed([K(1), K(2), K(3), 4])
    check(lambda: (2 in it, repr(list(it))), (True, "[K1]"), [(3, 2), (2, 2)])
    check(lambda: (5 in reversed((K(1),)), 5 not in reversed([K(5)])), (False, False), [(1, 5), (5, 5)])
    k = K(9)
    check(lambda: k in reversed([K(8), k, K(7)]), True, [(7, 9)])
    it = reversed([K(1), K(2)])
    next(it)
    check(lambda: (1 in it, list(it)), (True, []), [(1, 1)])
    check(lambda: [3 in reversed([K(3)]) for _ in range(2)], [True, True], [(3, 3), (3, 3)])
    check(lambda: (5 in reversed([1, "a"]), 1 in reversed((1, 2)), 0 in reversed([])), (False, True, False), [])
main()

check(lambda: 1 in reversed([K(1), K(2)]), True, [(2, 1), (1, 1)])
