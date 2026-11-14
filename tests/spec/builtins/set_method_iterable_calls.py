# spec: PLS-315 26.3.2
# description: a set's or frozenset's union, intersection, difference,
# their updates, isdisjoint and issuperset of an iterable that is not a set
# take its items in turn, hashing each and comparing it by a Python __eq__
# with the set's entries as SetAdd does: union adds each to a copy,
# difference discards it, intersection adds one found in the set to its
# result and stops once that is as large as the set, isdisjoint and
# issuperset stop at the item that decides; an error from __hash__ or
# __eq__ propagates, intersection_update then leaving the set unchanged,
# and intersection names an unhashable item's type alone; a set's own
# entries that compare by a Python __eq__ are compared with plain items
# once each; inside functions as at module level.
from harness import *

log = []

class K:
    def __init__(self, v): self.v = v
    def __hash__(self):
        log.append(("hash", self.v))
        return 0
    def __eq__(self, o):
        for _ in range(1): pass
        log.append(("eq", self.v, getattr(o, "v", o)))
        return isinstance(o, K) and o.v == self.v
    def __repr__(self): return "K%d" % self.v

class Bad(K):
    __hash__ = K.__hash__
    def __eq__(self, o): raise LookupError(self.v)

def gen(*vs):
    for v in vs:
        log.append(("gen", v))
        yield K(v)

def fresh():
    s = {K(1), K(2)}
    log.clear()
    return s

def shown(r):
    if isinstance(r, (set, frozenset)): return (type(r).__name__, sorted(r, key=repr))
    if isinstance(r, tuple): return tuple(shown(x) for x in r)
    return r

def attempt(f):
    try: r = f()
    except (TypeError, LookupError) as e: r = (type(e).__name__, str(e))
    return (shown(r), log[:])

def calls():
    for _ in range(1): pass
    out = {}
    s = fresh(); log.clear()
    out['union'] = attempt(lambda: s.union([K(2), K(3)]))
    s = fresh(); log.clear()
    out['union_gen'] = attempt(lambda: frozenset(s).union(gen(3, 1)))
    s = fresh(); log.clear()
    out['intersection'] = attempt(lambda: s.intersection([K(2), K(3), K(2)]))
    s = fresh(); log.clear()
    out['intersection_gen'] = attempt(lambda: s.intersection(gen(1)))
    s = fresh(); log.clear()
    out['intersection_stops'] = attempt(lambda: s.intersection(gen(2, 1, 4)))
    s = fresh(); log.clear()
    out['difference'] = attempt(lambda: s.difference([K(2)]))
    s = fresh(); log.clear()
    out['isdisjoint'] = attempt(lambda: s.isdisjoint(gen(3, 2, 1)))
    s = fresh(); log.clear()
    out['isdisjoint_true'] = attempt(lambda: s.isdisjoint([K(3)]))
    s = fresh(); log.clear()
    out['issuperset'] = attempt(lambda: s.issuperset(gen(1, 3, 2)))
    s = fresh(); log.clear()
    out['issuperset_true'] = attempt(lambda: s.issuperset([K(1)]))
    s = fresh(); log.clear()
    out['difference_update'] = attempt(lambda: (s.difference_update(gen(1)), s))
    s = fresh(); log.clear()
    out['intersection_update'] = attempt(lambda: (s.intersection_update(gen(2)), s))
    s = fresh(); log.clear()
    out['unhashable'] = attempt(lambda: s.union([[1]]))
    s = fresh(); log.clear()
    out['raising_eq'] = attempt(lambda: s.difference([Bad(1)]))
    s = fresh(); log.clear()
    out['raising_update'] = attempt(lambda: (s.intersection_update([K(2), Bad(1)]), s))
    return out

expected = {
    'union':
        "(('set', [K1, K2, K3]), [('hash', 2), ('eq', 1, 2), ('eq', 2, 2), "
        "('hash', 3), ('eq', 1, 3), ('eq', 2, 3)])",
    'union_gen':
        "(('frozenset', [K1, K2, K3]), [('gen', 3), ('hash', 3), ('eq', 1, "
        "3), ('eq', 2, 3), ('gen', 1), ('hash', 1), ('eq', 1, 1)])",
    'intersection':
        "(('set', [K2]), [('hash', 2), ('eq', 1, 2), ('eq', 2, 2), ('hash',"
        " 3), ('eq', 1, 3), ('eq', 2, 3), ('hash', 2), ('eq', 1, 2), ('eq',"
        " 2, 2), ('eq', 2, 2)])",
    'intersection_gen': "(('set', [K1]), [('gen', 1), ('hash', 1), ('eq', 1, 1)])",
    'intersection_stops':
        "(('set', [K1, K2]), [('gen', 2), ('hash', 2), ('eq', 1, 2), ('eq',"
        " 2, 2), ('gen', 1), ('hash', 1), ('eq', 1, 1), ('eq', 2, 1)])",
    'difference': "(('set', [K1]), [('hash', 2), ('eq', 1, 2), ('eq', 2, 2)])",
    'isdisjoint':
        "(False, [('gen', 3), ('hash', 3), ('eq', 1, 3), ('eq', 2, 3), "
        "('gen', 2), ('hash', 2), ('eq', 1, 2), ('eq', 2, 2)])",
    'isdisjoint_true': "(True, [('hash', 3), ('eq', 1, 3), ('eq', 2, 3)])",
    'issuperset':
        "(False, [('gen', 1), ('hash', 1), ('eq', 1, 1), ('gen', 3), "
        "('hash', 3), ('eq', 1, 3), ('eq', 2, 3)])",
    'issuperset_true': "(True, [('hash', 1), ('eq', 1, 1)])",
    'difference_update': "((None, ('set', [K2])), [('gen', 1), ('hash', 1), ('eq', 1, 1)])",
    'intersection_update':
        "((None, ('set', [K2])), [('gen', 2), ('hash', 2), ('eq', 1, 2), "
        "('eq', 2, 2)])",
    'unhashable': '((\'TypeError\', "cannot use \'list\' as a set element (unhashable type: \'list\')"), [])',
    'raising_eq': "(('LookupError', '1'), [('hash', 1)])",
    'raising_update':
        "(('LookupError', '1'), [('hash', 2), ('eq', 1, 2), ('eq', 2, 2), "
        "('hash', 1)])",
}
result = calls()
for name in expected: assert_eq(repr(result[name]), expected[name])

# At module level, and in a function that runs in C, too.
s = fresh()
r = s.intersection(gen(2, 1, 4))
assert_eq(repr((shown(r), log)), expected["intersection_stops"])
s = fresh()
r = s.union([K(2), K(3)])
assert_eq(repr((shown(r), log)), expected["union"])

def plain(s): return s.difference([K(2)])

s = fresh()
r = plain(s)
assert_eq(repr((shown(r), log)), expected["difference"])

# A set whose entries compare by a Python __eq__ compares an iterable's
# plain items with them, each once.
class E(int):
    def __eq__(self, o):
        for _ in range(1): pass
        log.append(("E", int(self), o))
        return int(self) == o
    __hash__ = int.__hash__

def entries():
    for _ in range(1): pass
    out = []
    for name in ("union", "intersection", "difference", "isdisjoint", "issuperset"):
        s = {E(1), E(2)}
        log.clear()
        r = getattr(s, name)([1, 3])
        out.append((name, sorted(r) if isinstance(r, set) else r, log[:]))
    return out

expected_entries = [
    ("union", [1, 2, 3], [("E", 1, 1)]),
    ("intersection", [1], [("E", 1, 1)]),
    ("difference", [2], [("E", 1, 1)]),
    ("isdisjoint", False, [("E", 1, 1)]),
    ("issuperset", False, [("E", 1, 1)]),
]
assert_eq(entries(), expected_entries)
s = {E(1), E(2)}
log.clear()
assert_eq((s.intersection([1, 3]), log), ({1}, [("E", 1, 1)]))
