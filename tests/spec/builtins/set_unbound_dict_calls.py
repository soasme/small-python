# spec: PLS-315 26.3.2
# description: set() and frozenset() of an exact dict add its keys with
# their stored hashes to an empty set, comparing them with one another;
# issubset of an exact dict hashes its keys and looks each up
# in the set until every element is found; symmetric_difference of one
# builds a set of its keys with their stored hashes, comparing them with
# one another, then toggles the set's elements in it. A set method
# called unbound, given its set first, compares as the bound one does,
# through Python __hash__ and __eq__ that loop; an exception from __eq__
# propagates.
from harness import *

log = []
class B:
    def __init__(s, v): s.v = v
    def __hash__(s):
        for _ in (): pass
        log.append(("h", s.v))
        return 1
    def __eq__(s, o):
        for _ in (): pass
        log.append(("e", s.v, o.v))
        return s.v == o.v
class SS(set): pass

def run(name, n1, n2, kind=set, other=dict.fromkeys):
    x = kind(B(v) for v in n1); y = other(B(v) for v in n2)
    del log[:]
    r = getattr(set, name)(x, y)
    if isinstance(r, (set, frozenset)): r = sorted(b.v for b in r)
    return r, log[:]

assert_eq(run("issubset", (1, 2), (1, 2, 3)),
          (True, [("h", 1), ("e", 1, 1), ("h", 2), ("e", 1, 2), ("e", 2, 2), ("e", 1, 2)]))
assert_eq(run("issubset", (1, 2, 3), (2,)), (False, [("h", 2), ("e", 1, 2), ("e", 2, 2)]))
assert_eq(run("issubset", (), (4,)), (True, [("h", 4)]))
assert_eq(run("issubset", (1,), (), SS), (False, []))
assert_eq(run("symmetric_difference", (1, 2), (1, 2, 3)),
          ([3], [("e", 1, 2), ("e", 1, 3), ("e", 2, 3), ("e", 1, 1), ("e", 2, 2)]))
assert_eq(run("symmetric_difference", (1, 2, 3), (2,), SS),
          ([1, 3], [("e", 2, 1), ("e", 2, 1), ("e", 2, 2), ("e", 1, 3), ("e", 1, 3)]))
assert_eq(run("symmetric_difference_update", (1, 2), (2,)), (None, [("e", 1, 2), ("e", 2, 2)]))

def unbound():
    out = []
    for name in ("union", "intersection", "difference", "isdisjoint", "issuperset", "update"):
        f = getattr(set, name)
        x = set(B(v) for v in (1, 2)); y = [B(2), B(3)]
        del log[:]
        r = f(x, y)
        out.append((name, sorted(b.v for b in r) if isinstance(r, set) else r, len(log)))
    return out
assert_eq(unbound(), [("union", [1, 2, 3], 6), ("intersection", [2], 6), ("difference", [1], 5),
                      ("isdisjoint", False, 3), ("issuperset", False, 6), ("update", None, 6)])

# symmetric_difference of a dict: its result is a set, or a frozenset of a
# frozenset's, and an exception from __eq__ propagates.
def toggled(kind, raising=False):
    x = kind(B(v) for v in (2, 4)); y = dict.fromkeys(B(v) for v in ((1, 9) if raising else (1, 2)))
    B.armed = raising
    del log[:]
    try: r = x.symmetric_difference(y)
    except LookupError as e: return str(e)
    finally: B.armed = False
    return type(r).__name__, sorted(b.v for b in r), len([e for e in log if e[0] == "e"])
B.armed = False
_eq = B.__eq__
def armed_eq(s, o):
    for _ in (): pass
    if B.armed and 9 in (s.v, o.v): raise LookupError("nine")
    return _eq(s, o)
B.__eq__ = armed_eq
class FS(frozenset): pass
assert_eq([toggled(set), toggled(SS), toggled(frozenset), toggled(FS)],
          [("set", [1, 4], 5), ("set", [1, 4], 5), ("frozenset", [1, 4], 5), ("frozenset", [1, 4], 5)])
assert_eq(toggled(set, True), "nine")

def built():
    d = dict.fromkeys(B(v) for v in (1, 2, 3))
    out = []
    for kind in (set, frozenset):
        del log[:]
        r = kind(d)
        out.append((type(r).__name__, sorted(b.v for b in r), log[:]))
    return out
assert_eq(built(), [("set", [1, 2, 3], [("e", 1, 2), ("e", 1, 3), ("e", 2, 3)]),
                    ("frozenset", [1, 2, 3], [("e", 1, 2), ("e", 1, 3), ("e", 2, 3)])])
