# spec: PLS-315 26.3.2
# description: union, intersection, difference and their updates of
# several sets take them in turn, as the method of each in order would:
# union adds each one's elements to a copy of the set, intersection
# intersects the result so far with each, difference takes the first's
# difference then discards each later one's elements from it, the updates
# change the set itself, intersection_update swapping the result in; a
# difference update by a set more than eight times larger discards their
# intersection's elements. Python __eq__ calls come in that order; on the
# machine, given the set first and bound, of sets, frozensets and a set
# subclass's instances.
from harness import *

log = []
class E:
    def __init__(self, v): self.v = v
    def __hash__(self): return 1
    def __eq__(self, o):
        for _ in (): pass
        log.append(self.v)
        return isinstance(o, E) and self.v == o.v
class S(set): pass
class H(E):
    def __hash__(self): return self.v
    __eq__ = E.__eq__
def mk(k, *v): return k(x if isinstance(x, E) else E(x) for x in v)
def shown(r): return (type(r).__name__, sorted(x.v for x in r)) if isinstance(r, (set, frozenset)) else r
def run():
    for _ in (): pass
    out = []
    for ka in (set, frozenset, S):
        for name in ("union", "intersection", "difference", "update", "intersection_update", "difference_update"):
            if not hasattr(ka, name): continue
            a = mk(ka, 1, 2, 3); b = mk(set, 2, 3, 4); c2 = mk(frozenset, 3, 5); d = mk(S, 1, 3)
            log.clear()
            r = getattr(a, name)(b, c2, d)
            out.append((ka.__name__, name, shown(r), shown(a), log[:]))
            a = mk(ka, 1, 2, 3); log.clear()
            r = getattr(ka, name)(a, mk(set, 3), mk(set, 1, 3))
            out.append((ka.__name__, name, shown(r), shown(a), log[:]))
    # a difference update by a much larger set
    for k in (set, S):
        a = mk(k, H(1), H(2)); big = set(map(H, range(1, 30))); log.clear()
        a -= big
        out.append(("-=", shown(a), len(log)))
        a = k([H(1), H(2), H(40)]); log.clear()
        a.difference_update(big)
        out.append(("du", shown(a), len(log)))
        a = k([H(1), H(2)]); log.clear()
        r = a.difference({H(5)}, big)
        out.append(("d", shown(r), len(log)))
    return out

expected = [('set', 'union', ('set', [1, 2, 3, 4, 5]), ('set', [1, 2, 3]), [1, 2, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 4, 1, 1, 2, 3]),
 ('set', 'union', ('set', [1, 2, 3]), ('set', [1, 2, 3]), [1, 1, 2, 3, 1, 1, 2, 3]),
 ('set', 'intersection', ('set', [3]), ('set', [1, 2, 3]), [1, 2, 1, 2, 3, 2, 1, 2, 3, 2, 3, 2, 3, 1, 3]),
 ('set', 'intersection', ('set', [3]), ('set', [1, 2, 3]), [1, 1, 2, 3, 1, 3]),
 ('set', 'difference', ('set', []), ('set', [1, 2, 3]), [2, 3, 4, 2, 2, 3, 1, 1, 1]),
 ('set', 'difference', ('set', [2]), ('set', [1, 2, 3]), [1, 3, 3, 1, 3, 1, 2]),
 ('set', 'update', None, ('set', [1, 2, 3, 4, 5]), [1, 2, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 4, 1, 1, 2, 3]),
 ('set', 'update', None, ('set', [1, 2, 3]), [1, 1, 2, 3, 1, 1, 2, 3]),
 ('set', 'intersection_update', None, ('set', [3]), [1, 2, 1, 2, 3, 2, 1, 2, 3, 2, 3, 2, 3, 1, 3]),
 ('set', 'intersection_update', None, ('set', [3]), [1, 1, 2, 3, 1, 3]),
 ('set', 'difference_update', None, ('set', []), [1, 2, 1, 3, 1, 1, 1, 1]),
 ('set', 'difference_update', None, ('set', [2]), [1, 1, 2, 3, 1, 2]),
 ('frozenset',
  'union',
  ('frozenset', [1, 2, 3, 4, 5]),
  ('frozenset', [1, 2, 3]),
  [1, 2, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 4, 1, 1, 2, 3]),
 ('frozenset', 'union', ('frozenset', [1, 2, 3]), ('frozenset', [1, 2, 3]), [1, 1, 2, 3, 1, 1, 2, 3]),
 ('frozenset', 'intersection', ('frozenset', [3]), ('frozenset', [1, 2, 3]), [1, 2, 1, 2, 3, 2, 1, 2, 3, 2, 3, 2, 3, 1, 3]),
 ('frozenset', 'intersection', ('frozenset', [3]), ('frozenset', [1, 2, 3]), [1, 1, 2, 3, 1, 3]),
 ('frozenset', 'difference', ('frozenset', []), ('frozenset', [1, 2, 3]), [2, 3, 4, 2, 2, 3, 1, 1, 1]),
 ('frozenset', 'difference', ('frozenset', [2]), ('frozenset', [1, 2, 3]), [1, 3, 3, 1, 3, 1, 2]),
 ('S', 'union', ('set', [1, 2, 3, 4, 5]), ('S', [1, 2, 3]), [1, 2, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 4, 1, 1, 2, 3]),
 ('S', 'union', ('set', [1, 2, 3]), ('S', [1, 2, 3]), [1, 1, 2, 3, 1, 1, 2, 3]),
 ('S', 'intersection', ('set', [3]), ('S', [1, 2, 3]), [1, 2, 1, 2, 3, 2, 1, 2, 3, 2, 3, 2, 3, 1, 3]),
 ('S', 'intersection', ('set', [3]), ('S', [1, 2, 3]), [1, 1, 2, 3, 1, 3]),
 ('S', 'difference', ('set', []), ('S', [1, 2, 3]), [2, 3, 4, 2, 2, 3, 1, 1, 1]),
 ('S', 'difference', ('set', [2]), ('S', [1, 2, 3]), [1, 3, 3, 1, 3, 1, 2]),
 ('S', 'update', None, ('S', [1, 2, 3, 4, 5]), [1, 2, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 4, 1, 1, 2, 3]),
 ('S', 'update', None, ('S', [1, 2, 3]), [1, 1, 2, 3, 1, 1, 2, 3]),
 ('S', 'intersection_update', None, ('S', [3]), [1, 2, 1, 2, 3, 2, 1, 2, 3, 2, 3, 2, 3, 1, 3]),
 ('S', 'intersection_update', None, ('S', [3]), [1, 1, 2, 3, 1, 3]),
 ('S', 'difference_update', None, ('S', []), [1, 2, 1, 3, 1, 1, 1, 1]),
 ('S', 'difference_update', None, ('S', [2]), [1, 1, 2, 3, 1, 2]),
 ('-=', ('set', []), 2),
 ('du', ('set', [40]), 2),
 ('d', ('set', []), 2),
 ('-=', ('S', []), 2),
 ('du', ('S', [40]), 2),
 ('d', ('set', []), 2)]
assert_eq(run(), expected)

# Without a loop, and an exception from __eq__ propagating.
def plain(a):
    log.clear()
    return shown(a.union(mk(set, 4), mk(set, 2))), shown(set.intersection(a, mk(set, 2), mk(set, 2, 3))), log[:]
assert_eq(plain(mk(set, 1, 2)), (("set", [1, 2, 4]), ("set", [2]), [1, 2, 1, 2, 2, 1, 2, 2]))
class Bad(E):
    __hash__ = E.__hash__
    def __eq__(self, o):
        for _ in (): pass
        raise KeyError(self.v)
def raising():
    for _ in (): pass
    s = mk(set, 1)
    try:
        s.update(mk(set, 2), {Bad(3)})
    except KeyError as e:
        return e.args, shown(s)
assert_eq(raising(), ((3,), ("set", [1, 2])))
