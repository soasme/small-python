# spec: PLS-315 26.3.2, 26.3.1
# description: a set's or frozenset's update, union, intersection,
# difference, their updates and issuperset of a list, a tuple, or an
# iterator over one, called as another call's argument, bound or unbound,
# on a set subclass's instance too, hash each item by its Python __hash__
# and compare it by its Python __eq__, both of which may loop, as a
# statement's call does; set(), frozenset() and a set display of a list
# iterator hash its items alike, and an exception from __hash__
# propagates. Inside functions as at module level.
from harness import *

log = []

class K:
    def __init__(self, v): self.v = v
    def __hash__(self):
        for _ in range(2): pass
        log.append(("h", self.v))
        if self.v < 0: raise ValueError(self.v)
        return self.v % 2
    def __eq__(self, other):
        for _ in range(2): pass
        log.append(("e", self.v, other.v))
        return self.v == other.v

class Sub(set): pass

def vals(s): return sorted(k.v for k in s) if isinstance(s, (set, frozenset)) else s

def error(f):
    try:
        return f()
    except ValueError as e:
        return "ValueError", e.args

def calls():
    del log[:]
    s, a = {K(1)}, K(2)
    i1, l1, t1 = iter([a, K(3)]), [a, K(3)], (K(3), K(4))
    i2, l2, i3, i4 = iter((K(1), K(5))), [K(4)], iter([K(3)]), iter([K(1)])
    i5, i6, i7, l3, i8 = iter([K(6), K(7)]), iter((K(8),)), iter([K(9), K(1)]), [K(-1)], iter([K(-2)])
    f, sub = frozenset({K(1)}), Sub([K(2)])
    del log[:]
    out = [vals(s.union(i1)), str(s.update(l1)), vals(s), vals(set.intersection(s, t1))]
    out += [vals(f.difference(i2)), vals(sub.union(l2)), str(Sub.difference_update(s, i3)), vals(s), set.issuperset(s, i4),
            vals(set(i5)), vals(frozenset(i6)), vals({*i7}), error(lambda: vals(s.union(l3))), error(lambda: str(s.update(i8))),
            vals(s), list(log)]
    return out

expected = [[1, 2, 3],
            'None',
            [1, 2, 3],
            [3],
            [],
            [2, 4],
            'None',
            [1, 2],
            True,
            [6, 7],
            [8],
            [1, 9],
            ('ValueError', (-1,)),
            ('ValueError', (-2,)),
            [1, 2],
            [('h', 2), ('h', 3), ('e', 1, 3), ('h', 2), ('h', 3), ('e', 1, 3), ('h', 3), ('e', 1, 3), ('e', 3, 3), ('h', 4),
             ('e', 2, 4), ('h', 1), ('e', 1, 1), ('h', 5), ('h', 4), ('e', 2, 4), ('h', 3), ('e', 1, 3), ('e', 3, 3), ('h', 1),
             ('e', 1, 1), ('h', 6), ('h', 7), ('h', 8), ('h', 9), ('h', 1), ('e', 9, 1), ('h', -1), ('h', -2)]]

def main():
    return calls()

assert_eq(main(), expected)
assert_eq(calls(), expected)
