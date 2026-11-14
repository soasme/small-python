# spec: PLS-315 26.3.2, 7.4
# description: a set's operator, reflected operator, in-place operator and
# rich comparison methods called by name, bound or on the type with the set
# first, compare elements as the operators do (26.3.2): the same Python
# __eq__ calls in the same order, the result of the left operand's type, a
# reflected method's operands swapped, an in-place method's result the set
# itself, changed. Given a non-set such a method returns NotImplemented; a
# method of frozenset rejects a set. An exception from __eq__ propagates.
# Inside functions, with and without loops, as at module level.
from harness import *

log = []

class E:
    def __init__(self, v): self.v = v
    def __hash__(self): return 1
    def __eq__(self, o):
        log.append(self.v)
        if self.v == 9: raise KeyError(9)
        return isinstance(o, E) and self.v == o.v

def mk(*v):
    return {E(x) for x in v}

def shown(r):
    return (type(r).__name__, sorted(x.v for x in r)) if isinstance(r, (set, frozenset)) else r

NAMES = ("__or__", "__and__", "__sub__", "__xor__", "__ror__", "__rand__", "__rsub__", "__rxor__",
         "__eq__", "__ne__", "__lt__", "__le__", "__gt__", "__ge__")

expected = [
    ("__or__", ("set", [1, 2, 3, 4]), [1, 2, 1, 2, 3, 1, 2, 3]),
    ("__and__", ("set", [2, 3]), [1, 2, 1, 2, 3, 2, 1, 2, 3]),
    ("__sub__", ("set", [1]), [2, 3, 4, 2, 2, 3]),
    ("__xor__", ("set", [1, 4]), [2, 3, 4, 2, 3, 4, 2, 3]),
    ("__ror__", ("frozenset", [1, 2, 3, 4]), [2, 3, 4, 2, 2, 3]),
    ("__rand__", ("frozenset", [2, 3]), [2, 3, 4, 2, 2, 3, 2]),
    ("__rsub__", ("frozenset", [4]), [1, 2, 1, 2, 3, 1, 2, 3]),
    ("__rxor__", ("frozenset", [1, 4]), [1, 2, 1, 3, 1, 1]),
    ("__eq__", False, [2, 3, 4]),
    ("__ne__", True, [2, 3, 4]),
    ("__lt__", False, []),
    ("__le__", False, [2, 3, 4]),
    ("__gt__", False, []),
    ("__ge__", False, [1, 2, 1, 2, 3, 1, 2, 3]),
]
expected_inplace = [
    ("__ior__", True, ("set", [1, 2, 3, 4]), [2, 2, 3, 1, 2, 1, 2, 3, 1, 2, 3]),
    ("__iand__", True, ("set", [2, 3]), [2, 2, 3, 1, 2, 1, 2, 3, 2, 1, 2, 3]),
    ("__isub__", True, ("set", [1]), [2, 2, 3, 1, 2, 1, 3, 1]),
    ("__ixor__", True, ("set", [1, 4]), [2, 2, 3, 1, 2, 1, 3, 1, 1]),
]

def looped(unbound):
    out = []
    for name in NAMES:
        a, b = mk(1, 2, 3), frozenset(mk(2, 3, 4))
        log.clear()
        out.append((name, shown(getattr(set, name)(a, b) if unbound else getattr(a, name)(b)), log[:]))
    for name in ("__ior__", "__iand__", "__isub__", "__ixor__"):
        x = mk(1, 2, 3)
        log.clear()
        out.append((name, getattr(x, name)(frozenset(mk(2, 3, 4))) is x, shown(x), log[:]))
    return out

assert_eq(looped(False), expected + expected_inplace)
assert_eq(looped(True), expected + expected_inplace)

# Without a loop, and at module level.
def plain(a, b):
    log.clear()
    return [shown(a.__and__(b)), shown(set.__rsub__(a, b)), a.__eq__(b), set.__le__(a, b), a.__ixor__(b) is a, shown(a), log[:]]

expected_plain = [("set", [2]), ("set", [5]), False, False, True, ("set", [1, 5]),
                  [1, 2, 1, 2, 1, 2, 1, 2, 2, 5, 2, 5, 1, 2, 1, 1]]
assert_eq(plain(mk(1, 2), mk(2, 5)), expected_plain)
a, b = mk(1, 2), mk(2, 5)
log.clear()
assert_eq([shown(a.__and__(b)), shown(set.__rsub__(a, b)), a.__eq__(b), set.__le__(a, b), a.__ixor__(b) is a, shown(a), log[:]],
          expected_plain)

# A non-set gives NotImplemented; frozenset's method rejects a set; an
# exception from __eq__ propagates.
assert_eq((set.__or__(mk(1), [1]), mk(1).__le__([1]), shown(frozenset.__and__(frozenset(), set()))),
          (NotImplemented, NotImplemented, ("frozenset", [])))
assert_raises(TypeError, lambda: frozenset.__or__(set(), frozenset()))
def raising():
    for _ in range(1): pass
    return mk(9).__and__(mk(1))
assert_raises(KeyError, raising)
assert_raises(KeyError, lambda: mk(9).__isub__(mk(1)))
