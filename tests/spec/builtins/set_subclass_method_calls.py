# spec: PLS-315 26.3.2
# description: the union, intersection, difference, their updates,
# symmetric_difference_update, issubset, issuperset and isdisjoint of an
# instance of a subclass of set or frozenset that defines no method run on
# its set: each item of an iterable that is not a set is hashed by its
# Python __hash__ and compared by its Python __eq__, both of which may
# loop, as the set's own method does; a result is a set or frozenset, an
# update changes the instance, and an exception from __hash__ or __eq__
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
        if other.v == 7: raise LookupError(self.v)
        return self.v == other.v

class Sub(set): pass
class FSub(frozenset): pass

def vals(s): return (type(s).__name__, sorted(k.v for k in s)) if isinstance(s, (set, frozenset)) else s

NAMES = ["update", "union", "intersection", "difference", "intersection_update", "difference_update",
         "symmetric_difference_update", "issubset", "issuperset", "isdisjoint"]

def calls():
    out = []
    for name in NAMES:
        for kind in (Sub, FSub):
            if kind is FSub and name.endswith("update"): continue
            s = kind([K(1), K(2)])
            del log[:]
            r = getattr(s, name)([K(2), K(3), K(5)])
            out.append((name, kind.__name__, vals(r), vals(s), list(log)))
            for bad in (K(-1), K(7)):
                del log[:]
                try:
                    getattr(s, name)([bad])
                except (ValueError, LookupError) as e:
                    out.append((type(e).__name__, vals(s), list(log)))
    return out

expected = [
    ('update', 'Sub', None, ('Sub', [1, 2, 3, 5]), [('h', 2), ('e', 2, 2), ('h', 3), ('e', 1, 3), ('h', 5), ('e', 1, 5), ('e', 3, 5)]),
    ('ValueError', ('Sub', [1, 2, 3, 5]), [('h', -1)]),
    ('LookupError', ('Sub', [1, 2, 3, 5]), [('h', 7), ('e', 1, 7)]),
    ('union', 'Sub', ('set', [1, 2, 3, 5]), ('Sub', [1, 2]), [('h', 2), ('e', 2, 2), ('h', 3), ('e', 1, 3), ('h', 5), ('e', 1, 5), ('e', 3, 5)]),
    ('ValueError', ('Sub', [1, 2]), [('h', -1)]),
    ('LookupError', ('Sub', [1, 2]), [('h', 7), ('e', 1, 7)]),
    ('union', 'FSub', ('frozenset', [1, 2, 3, 5]), ('FSub', [1, 2]), [('h', 2), ('e', 2, 2), ('h', 3), ('e', 1, 3), ('h', 5), ('e', 1, 5), ('e', 3, 5)]),
    ('ValueError', ('FSub', [1, 2]), [('h', -1)]),
    ('LookupError', ('FSub', [1, 2]), [('h', 7), ('e', 1, 7)]),
    ('intersection', 'Sub', ('set', [2]), ('Sub', [1, 2]), [('h', 2), ('e', 2, 2), ('h', 3), ('e', 1, 3), ('h', 5), ('e', 1, 5)]),
    ('ValueError', ('Sub', [1, 2]), [('h', -1)]),
    ('LookupError', ('Sub', [1, 2]), [('h', 7), ('e', 1, 7)]),
    ('intersection', 'FSub', ('frozenset', [2]), ('FSub', [1, 2]), [('h', 2), ('e', 2, 2), ('h', 3), ('e', 1, 3), ('h', 5), ('e', 1, 5)]),
    ('ValueError', ('FSub', [1, 2]), [('h', -1)]),
    ('LookupError', ('FSub', [1, 2]), [('h', 7), ('e', 1, 7)]),
    ('difference', 'Sub', ('set', [1]), ('Sub', [1, 2]), [('h', 2), ('e', 2, 2), ('h', 3), ('e', 1, 3), ('h', 5), ('e', 1, 5)]),
    ('ValueError', ('Sub', [1, 2]), [('h', -1)]),
    ('LookupError', ('Sub', [1, 2]), [('h', 7), ('e', 1, 7)]),
    ('difference', 'FSub', ('frozenset', [1]), ('FSub', [1, 2]), [('h', 2), ('e', 2, 2), ('h', 3), ('e', 1, 3), ('h', 5), ('e', 1, 5)]),
    ('ValueError', ('FSub', [1, 2]), [('h', -1)]),
    ('LookupError', ('FSub', [1, 2]), [('h', 7), ('e', 1, 7)]),
    ('intersection_update', 'Sub', None, ('Sub', [2]), [('h', 2), ('e', 2, 2), ('h', 3), ('e', 1, 3), ('h', 5), ('e', 1, 5)]),
    ('ValueError', ('Sub', [2]), [('h', -1)]),
    ('difference_update', 'Sub', None, ('Sub', [1]), [('h', 2), ('e', 2, 2), ('h', 3), ('e', 1, 3), ('h', 5), ('e', 1, 5)]),
    ('ValueError', ('Sub', [1]), [('h', -1)]),
    ('LookupError', ('Sub', [1]), [('h', 7), ('e', 1, 7)]),
    ('symmetric_difference_update', 'Sub', None, ('Sub', [1, 3, 5]), [('h', 2), ('h', 3), ('h', 5), ('e', 3, 5), ('e', 2, 2), ('e', 1, 3), ('e', 1, 3), ('e', 1, 5), ('e', 3, 5), ('e', 1, 5), ('e', 3, 5)]),
    ('ValueError', ('Sub', [1, 3, 5]), [('h', -1)]),
    ('LookupError', ('Sub', [1, 3, 5]), [('h', 7), ('e', 1, 7)]),
    ('issubset', 'Sub', False, ('Sub', [1, 2]), [('h', 2), ('e', 2, 2), ('h', 3), ('e', 1, 3), ('h', 5), ('e', 1, 5)]),
    ('ValueError', ('Sub', [1, 2]), [('h', -1)]),
    ('LookupError', ('Sub', [1, 2]), [('h', 7), ('e', 1, 7)]),
    ('issubset', 'FSub', False, ('FSub', [1, 2]), [('h', 2), ('e', 2, 2), ('h', 3), ('e', 1, 3), ('h', 5), ('e', 1, 5)]),
    ('ValueError', ('FSub', [1, 2]), [('h', -1)]),
    ('LookupError', ('FSub', [1, 2]), [('h', 7), ('e', 1, 7)]),
    ('issuperset', 'Sub', False, ('Sub', [1, 2]), [('h', 2), ('e', 2, 2), ('h', 3), ('e', 1, 3)]),
    ('ValueError', ('Sub', [1, 2]), [('h', -1)]),
    ('LookupError', ('Sub', [1, 2]), [('h', 7), ('e', 1, 7)]),
    ('issuperset', 'FSub', False, ('FSub', [1, 2]), [('h', 2), ('e', 2, 2), ('h', 3), ('e', 1, 3)]),
    ('ValueError', ('FSub', [1, 2]), [('h', -1)]),
    ('LookupError', ('FSub', [1, 2]), [('h', 7), ('e', 1, 7)]),
    ('isdisjoint', 'Sub', False, ('Sub', [1, 2]), [('h', 2), ('e', 2, 2)]),
    ('ValueError', ('Sub', [1, 2]), [('h', -1)]),
    ('LookupError', ('Sub', [1, 2]), [('h', 7), ('e', 1, 7)]),
    ('isdisjoint', 'FSub', False, ('FSub', [1, 2]), [('h', 2), ('e', 2, 2)]),
    ('ValueError', ('FSub', [1, 2]), [('h', -1)]),
    ('LookupError', ('FSub', [1, 2]), [('h', 7), ('e', 1, 7)]),
]

def main():
    return calls()

assert_eq(main(), expected)
assert_eq(calls(), expected)
