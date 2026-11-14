# spec: PLS-315 26.3.2
# description: a set method given an exact dict or frozendict takes its
# keys as the dict stores them: union, update and
# symmetric_difference_update look each key up by its stored hash, calling
# no __hash__, and difference looks each of the set's elements up in the
# dict unless the set is more than four times larger; intersection,
# issuperset, isdisjoint, difference_update and the larger difference hash
# each key in turn, as for any iterable; a dict subclass's keys are hashed
# as any iterable's. Each lookup compares by the stored element's Python
# __eq__. Inside functions as at module level.
from harness import *

log = []

class E:
    def __init__(self, v): self.v = v
    def __hash__(self):
        for _ in (): pass
        log.append(("h", self.v))
        return 1
    def __eq__(self, other):
        for _ in (): pass
        log.append(("e", self.v, other.v))
        return self.v == other.v

class DS(dict): pass

def mk(): return {E(1), E(2)}
def dk(): return {E(2): 0, E(3): 0}

def calls(kind):
    out = []
    for name in ("union", "intersection", "difference", "issuperset", "isdisjoint",
                 "update", "intersection_update", "difference_update", "symmetric_difference_update"):
        a = mk(); d = kind(dk()); log.clear()
        r = getattr(a, name)(d)
        out.append((name, r if type(r) is bool else sorted(x.v for x in (a if r is None else r)), log[:]))
    log.clear()
    return out

expected = [
    ("union", [1, 2, 3], [("e", 1, 2), ("e", 2, 2), ("e", 1, 3), ("e", 2, 3)]),
    ("intersection", [2], [("h", 2), ("e", 1, 2), ("e", 2, 2), ("h", 3), ("e", 1, 3), ("e", 2, 3)]),
    ("difference", [1], [("e", 2, 1), ("e", 3, 1), ("e", 2, 2)]),
    ("issuperset", False, [("h", 2), ("e", 1, 2), ("e", 2, 2), ("h", 3), ("e", 1, 3), ("e", 2, 3)]),
    ("isdisjoint", False, [("h", 2), ("e", 1, 2), ("e", 2, 2)]),
    ("update", [1, 2, 3], [("e", 1, 2), ("e", 2, 2), ("e", 1, 3), ("e", 2, 3)]),
    ("intersection_update", [2], [("h", 2), ("e", 1, 2), ("e", 2, 2), ("h", 3), ("e", 1, 3), ("e", 2, 3)]),
    ("difference_update", [1], [("h", 2), ("e", 1, 2), ("e", 2, 2), ("h", 3), ("e", 1, 3)]),
    ("symmetric_difference_update", [1, 3], [("e", 1, 2), ("e", 2, 2), ("e", 1, 3), ("e", 1, 3)]),
]
assert_eq(calls(dict), expected)
assert_eq(calls(frozendict), expected)

# A set more than four times larger than the dict hashes its keys.
def larger():
    a = {E(1), 10, 11, 12, 13, 14, 15, 16}
    d = {E(4): 0}
    log.clear()
    r = a.difference(d)
    return (len(r), log[:])

assert_eq(larger(), (8, [("h", 4), ("e", 1, 4)]))
log.clear()

# A dict subclass is iterated, its keys hashed.
def subclass():
    a = mk(); d = DS(dk()); log.clear()
    a.update(d)
    return (sorted(x.v for x in a), log[:])

assert_eq(subclass(), ([1, 2, 3], [("h", 2), ("e", 1, 2), ("e", 2, 2), ("h", 3), ("e", 1, 3), ("e", 2, 3)]))
log.clear()

# An error from __eq__ propagates from the method, the set unchanged by update.
class Bad(E):
    __hash__ = E.__hash__
    def __eq__(self, other):
        for _ in (): pass
        raise LookupError(self.v)

def errors():
    out = []
    for name in ("union", "update", "difference", "symmetric_difference_update"):
        a = {Bad(1)}
        try: getattr(a, name)({E(2): 0})
        except LookupError as e: out.append((name, e.args, len(a)))
    return out

assert_eq(errors(), [("union", (1,), 1), ("update", (1,), 1), ("difference", (1,), 1), ("symmetric_difference_update", (1,), 1)])
