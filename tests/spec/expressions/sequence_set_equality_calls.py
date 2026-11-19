# spec: PLS-315 6.10.1 26.3.2 26.1.2
# description: == and != of two tuples, lists or dicts compare their
# items in order; an item pair of two sets or frozensets compares as the
# sets do, looking each element of one up in the other, an element's
# Python __eq__ called on a matching hash, so the comparison goes on
# after it or stops at an unequal pair; an error of __eq__ propagates.
from harness import *

log = []
class K:
    def __init__(self, v): self.v = v
    def __hash__(self): return self.v
    def __eq__(self, other):
        for _ in (): pass
        log.append(("eq", self.v))
        if self.v < 0: raise LookupError("eq")
        return isinstance(other, K) and other.v == self.v

def attempt(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))

def results():
    for _ in (): pass
    del log[:]
    a, b = K(1), K(2)
    out = [(1, {a}) == (1, {K(1)}), [{a}, {b}] != [{K(1)}, {K(2)}], (frozenset({a}), 2) == ({K(1)}, 3),
           {"k": {b}} == {"k": {K(2)}}, ((0, {a}),) == ((0, {K(3)}),), ({a}, {b}) == ({K(1)}, {K(5)}),
           attempt(lambda: (1, {K(-1)}) == (1, {K(-1)}))]
    return out, list(log)

expected = ([True, False, False, True, False, False, ("LookupError", "eq")],
            [("eq", 1), ("eq", 1), ("eq", 2), ("eq", 1), ("eq", 2), ("eq", 1), ("eq", -1)])

assert_eq(results(), expected)
assert_eq(results(), expected)
