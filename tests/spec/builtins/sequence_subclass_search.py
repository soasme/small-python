# spec: PLS-315 26.2.3, 7.8.2
# description: index, count and remove of a list or tuple subclass's
# instance, bound or called on the class, compare each item with the value
# by the item's Python __eq__, which may loop, mutate the sequence or
# return NotImplemented, before the value's reflected one; errors propagate.
from harness import *

log = []
class X:
    def __init__(self, n): self.n = n
    def __eq__(self, other):
        for _ in range(2): pass
        log.append(self.n)
        if self.n == 9: raise LookupError("eq")
        return NotImplemented if self.n == 0 else self.n == other
class L(list): pass
class T(tuple): pass

def run(f):
    del log[:]
    try:
        return f(), log[:]
    except Exception as e:
        return type(e).__name__, log[:]

def cases():
    l = L([X(1), X(0), X(2)])
    return [run(lambda: l.index(2)), run(lambda: l.count(1)), run(lambda: L.index(l, 2, 1)),
            run(lambda: T((X(3), X(4))).index(4)), run(lambda: T.count(T((X(5),)), 5)),
            run(lambda: (l.remove(2), len(l))), run(lambda: L([X(1)]).index(7)),
            run(lambda: L([X(9)]).count(1))]
expected = [(2, [1, 0, 2]), (1, [1, 0, 2]), (2, [0, 2]), (1, [3, 4]), (1, [5]),
            ((None, 2), [1, 0, 2]), ("ValueError", [1]), ("LookupError", [9])]
assert_eq(cases(), expected)
def gen():
    yield cases()
assert_eq(next(gen()), expected)
