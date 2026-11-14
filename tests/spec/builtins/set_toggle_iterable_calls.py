# spec: PLS-315 26.3.2, 26.3.1
# description: a set's or frozenset's symmetric_difference and a set's
# symmetric_difference_update of an iterable that is not a set make a set
# of its items, hashing each and comparing it with the items of equal hash
# before it, then toggle, as ^ and ^= do: symmetric_difference looks each
# of the set's elements up in that set, removing one found and adding one
# missing after a second lookup, its result of the set's type;
# symmetric_difference_update so looks each of that set's elements up in
# the set itself. issubset of such an iterable is whether the intersection
# with it has all the set's elements, the iterable taken only until it
# does. Python __hash__ and __eq__ calls come in that order; an exception
# from one propagates. Inside functions, with and without loops, as at
# module level.
from harness import *

log = []

class E:
    def __init__(self, v): self.v = v
    def __hash__(self):
        log.append(("h", self.v))
        return 1
    def __eq__(self, o):
        log.append(self.v)
        if self.v == 9: raise KeyError(9)
        return isinstance(o, E) and self.v == o.v

def shown(r):
    return (type(r).__name__, sorted(x.v for x in r)) if isinstance(r, (set, frozenset)) else r

def gen(*v):
    for x in v: yield E(x)

SOURCES = (lambda: [E(2), E(4), E(2)], lambda: gen(2, 4), lambda: (E(1), E(2), E(5)))

def cases():
    out = []
    for kind in (set, frozenset):
        for src in SOURCES:
            for name in ("symmetric_difference", "issubset") + (("symmetric_difference_update",) if kind is set else ()):
                a = kind(E(x) for x in (1, 2, 3))
                s = src()
                log.clear()
                r = getattr(a, name)(s)
                out.append((kind.__name__, name, shown(r), shown(a), log[:]))
    return out

expected = [
    ('set', 'symmetric_difference', ('set', [1, 3, 4]), ('set', [1, 2, 3]), [('h', 2), ('h', 4), 2, ('h', 2), 2, 2, 4, 2, 4, 2, 4, 1, 4, 1]),
    ('set', 'issubset', False, ('set', [1, 2, 3]), [('h', 2), 1, 2, ('h', 4), 1, 2, 3, ('h', 2), 1, 2, 2]),
    ('set', 'symmetric_difference_update', None, ('set', [1, 3, 4]), [('h', 2), ('h', 4), 2, ('h', 2), 2, 1, 2, 1, 3, 1, 3]),
    ('set', 'symmetric_difference', ('set', [1, 3, 4]), ('set', [1, 2, 3]), [('h', 2), ('h', 4), 2, 2, 4, 2, 4, 2, 4, 1, 4, 1]),
    ('set', 'issubset', False, ('set', [1, 2, 3]), [('h', 2), 1, 2, ('h', 4), 1, 2, 3]),
    ('set', 'symmetric_difference_update', None, ('set', [1, 3, 4]), [('h', 2), ('h', 4), 2, 1, 2, 1, 3, 1, 3]),
    ('set', 'symmetric_difference', ('set', [3, 5]), ('set', [1, 2, 3]), [('h', 1), ('h', 2), 1, ('h', 5), 1, 2, 1, 2, 5, 5]),
    ('set', 'issubset', False, ('set', [1, 2, 3]), [('h', 1), 1, ('h', 2), 1, 2, 1, ('h', 5), 1, 2, 3]),
    ('set', 'symmetric_difference_update', None, ('set', [3, 5]), [('h', 1), ('h', 2), 1, ('h', 5), 1, 2, 1, 2, 3, 3]),
    ('frozenset', 'symmetric_difference', ('frozenset', [1, 3, 4]), ('frozenset', [1, 2, 3]), [('h', 2), ('h', 4), 2, ('h', 2), 2, 2, 4, 2, 4, 2, 4, 1, 4, 1]),
    ('frozenset', 'issubset', False, ('frozenset', [1, 2, 3]), [('h', 2), 1, 2, ('h', 4), 1, 2, 3, ('h', 2), 1, 2, 2]),
    ('frozenset', 'symmetric_difference', ('frozenset', [1, 3, 4]), ('frozenset', [1, 2, 3]), [('h', 2), ('h', 4), 2, 2, 4, 2, 4, 2, 4, 1, 4, 1]),
    ('frozenset', 'issubset', False, ('frozenset', [1, 2, 3]), [('h', 2), 1, 2, ('h', 4), 1, 2, 3]),
    ('frozenset', 'symmetric_difference', ('frozenset', [3, 5]), ('frozenset', [1, 2, 3]), [('h', 1), ('h', 2), 1, ('h', 5), 1, 2, 1, 2, 5, 5]),
    ('frozenset', 'issubset', False, ('frozenset', [1, 2, 3]), [('h', 1), 1, ('h', 2), 1, 2, 1, ('h', 5), 1, 2, 3]),
]
assert_eq(cases(), expected)

# Without a loop, and at module level.
def plain(a):
    log.clear()
    r = [shown(a.symmetric_difference([E(2), E(5)])), a.issubset((E(3), E(1))), a.symmetric_difference_update([E(1)]), shown(a)]
    return r + [log[:]]

expected_plain = [("set", [1, 2, 3, 5]), True, None, ("set", [3]),
                  [("h", 2), ("h", 5), 2, 2, 5, 2, 5, 2, 5, 1, 2, 5, 1, ("h", 3), 1, 3, ("h", 1), 1, 3, ("h", 1), 1]]
assert_eq(plain({E(1), E(3)}), expected_plain)
a = {E(1), E(3)}
log.clear()
assert_eq([shown(a.symmetric_difference([E(2), E(5)])), a.issubset((E(3), E(1))), a.symmetric_difference_update([E(1)]), shown(a), log[:]],
          expected_plain)

# An exception from __eq__ propagates; the set is unchanged by a failed
# symmetric_difference.
a = {E(1)}
assert_raises(KeyError, lambda: a.symmetric_difference([E(9), E(9)]))
assert_eq(shown(a), ("set", [1]))
assert_raises(KeyError, lambda: {E(9)}.symmetric_difference_update([E(1)]))
def raising():
    for _ in range(1): pass
    return {E(9)}.issubset([E(1)])
assert_raises(KeyError, raising)
assert_eq((shown(set().symmetric_difference([E(1)])), set().issubset([]), {E(1)}.issubset([])), (("set", [1]), True, False))
