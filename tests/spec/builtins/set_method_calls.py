# spec: PLS-315 26.3.1, 26.3.2
# description: A set's union, intersection, difference and
# symmetric_difference methods, their updates, and issubset, issuperset and
# isdisjoint,
# given one set or frozenset, bound or called on the type with the set
# first, find equal elements by hash and then by ==, as their operators do,
# so an element's Python __eq__ is called with an element of equal hash;
# an exception from it propagates out of the call. The result has the
# set's type; an update changes the set in place and returns None. A set's
# elements merged into an empty set are not compared with one another
# (Annex D). Inside functions as at module level.
from harness import *

log = []

class P:
    def __init__(self, v): self.v = v
    def __hash__(self): return self.v % 3
    def __eq__(self, other):
        log.append(self.v)
        if 9 in (self.v, getattr(other, "v", 0)): raise KeyError(9)
        return isinstance(other, P) and self.v == other.v
    def __repr__(self): return "P%d" % self.v

def names(s):
    return type(s).__name__, sorted(map(repr, s))

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def methods():
    a, b = {P(1), P(2), P(4), 7}, frozenset({P(1), P(5), 3})
    out = []
    for name in ("union", "intersection", "difference", "symmetric_difference", "issubset", "issuperset", "isdisjoint"):
        bound, unbound = getattr(a, name)(b), getattr(set, name)(a, b)
        out.append(bound if isinstance(bound, bool) else names(bound))
        out.append(bound == unbound)
    del log[:]
    out += [names(a.union({P(4)})), bool(log), names(frozenset(b).difference({P(5)})),
            {P(1)}.issubset(a), a.issuperset({P(2), P(5)}), a.issubset(a | b),
            a.isdisjoint({P(5), P(8)}), frozenset({P(10), P(4)}).isdisjoint(a)]
    for name in ("update", "intersection_update", "difference_update", "symmetric_difference_update"):
        s = set(a)
        out.append((getattr(s, name)(b), names(s)))
        s = set(a)
        out.append((getattr(set, name)(s, {P(1)}), names(s)))
    out += [error(lambda: {P(9)}.union({P(0)})), error(lambda: set.intersection({P(0)}, {P(9)})),
            error(lambda: {P(3)}.issubset({P(9)})), error(lambda: {P(9)}.isdisjoint({P(0), P(3)})),
            error(lambda: set.union(frozenset(), {P(1)}))]
    s = {P(9)}
    out.append((error(lambda: s.update({P(0)})), names(s)))
    return out

expected = [("set", ["3", "7", "P1", "P2", "P4", "P5"]), True, ("set", ["P1"]), True, ("set", ["7", "P2", "P4"]), True,
            ("set", ["3", "7", "P2", "P4", "P5"]), True, False, True, False, True, False, True,
            ("set", ["7", "P1", "P2", "P4"]), True, ("frozenset", ["3", "P1"]), True, False, True, True, False,
            (None, ("set", ["3", "7", "P1", "P2", "P4", "P5"])), (None, ("set", ["7", "P1", "P2", "P4"])),
            (None, ("set", ["P1"])), (None, ("set", ["P1"])), (None, ("set", ["7", "P2", "P4"])),
            (None, ("set", ["7", "P2", "P4"])), (None, ("set", ["3", "7", "P2", "P4", "P5"])),
            (None, ("set", ["7", "P2", "P4"])), ("KeyError", "9"), ("KeyError", "9"), ("KeyError", "9"), ("KeyError", "9"),
            ("TypeError", "descriptor 'union' for 'set' objects doesn't apply to a 'frozenset' object"),
            (("KeyError", "9"), ("set", ["P9"]))]
assert_eq(methods(), expected)
assert_eq(methods(), expected)

# Merging a set's elements into an empty set compares none of them.
def merged():
    a = {P(1), P(4), P(7)}
    del log[:]
    out = [names(set(a)), names(frozenset(a)), names({*a}), names(set().union(a)), names(frozenset() | a)]
    s = set()
    s.update(a)
    t = set()
    t |= a
    out += [names(s), names(t), log[:]]
    return out

expected_merged = [("set", ["P1", "P4", "P7"]), ("frozenset", ["P1", "P4", "P7"]), ("set", ["P1", "P4", "P7"]),
                   ("set", ["P1", "P4", "P7"]), ("frozenset", ["P1", "P4", "P7"]), ("set", ["P1", "P4", "P7"]),
                   ("set", ["P1", "P4", "P7"]), []]
assert_eq(merged(), expected_merged)
a = {P(1), P(4)}
del log[:]
assert_eq((names(set(a)), log), (("set", ["P1", "P4"]), []))
