# spec: PLS-315 7.8.3, 13.10
# description: x in a forward iterator over a list or tuple compares the
# items it has left with x as v == x, in order: an item's __eq__, which may
# loop, sees x itself; the items before it compare natively, the first true
# result stops the search with the iterator just past the match, and a
# search that finds nothing exhausts it. In an expression, an if test and a
# comparison chain, inside functions as at module level.
from harness import *

log = []
class Key:
    def __init__(self, n): self.n = n
    def __eq__(self, other):
        for _ in (): pass
        log.append(("eq", self.n, type(other).__name__))
        return self.n == other
    __hash__ = None
def searches():
    del log[:]
    out = []
    it = iter([1, Key(2), Key(3), Key(4)])
    out += [3 in it, [k.n for k in it], list(log)]
    del log[:]
    it = iter((Key(5),))
    out += [b"x" in it, list(it), list(log)]
    del log[:]
    it = iter([0, Key(1)]); next(it)
    out += [1 in it, list(log)]
    del log[:]
    it = iter([Key(1), Key(2)])
    tests = []
    if 2 in it: tests.append("in")
    if 9 not in iter([Key(9)]): tests.append("never")
    out += [tests, 0 < 2 in iter([Key(2)]), list(log)]
    return out

expected = [True, [4], [('eq', 2, 'int'), ('eq', 3, 'int')], False, [], [('eq', 5, 'bytes')], True, [('eq', 1, 'int')], ['in'], True, [('eq', 1, 'int'), ('eq', 2, 'int'), ('eq', 9, 'int'), ('eq', 2, 'int')]]
assert_eq(searches(), expected)

def nested():
    return searches()

assert_eq(nested(), expected)
