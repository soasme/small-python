# spec: PLS-315 26.1.1, 26.1.3
# description: dict(x, **kw), a dict subclass's call and d.update(x, **kw)
# take x's items first, the pairs of a Python __iter__ or the keys and
# values of a Python keys and __getitem__, each of which may loop, then
# the keywords in their order, a keyword replacing an item of the same
# key; keywords may be named or unpacked. An exception from x leaves the
# keywords unmerged, d keeping the items before it. Inside functions as
# at module level.
from harness import *

log = []

class Pairs:
    def __init__(self, items): self.items = items
    def __iter__(self):
        for _ in (): pass
        log.append("iter")
        return iter(self.items)

class Keyed:
    def keys(self):
        for _ in (): pass
        log.append("keys")
        return ["a", "b"]
    def __getitem__(self, k):
        for _ in (): pass
        log.append(k)
        return k * 2

class Gen:
    def __iter__(self):
        for _ in (): pass
        yield "a", 1
        raise LookupError("gen")

class Sub(dict): pass

def run():
    e = {"q": 0}; g = {}
    kw = {"b": 7, "c": 8}
    e.update(Pairs([("y", 1), ("q", 2)]), y=3)
    g.update(Keyed(), **kw)
    s = Sub(Pairs([("s", 1)]), t=2)
    return [dict(Pairs([("a", 1), ("z", 0)]), z=1, w=2), e, dict(Keyed(), a=0), g, s, type(s).__name__]

expected = [{"a": 1, "z": 1, "w": 2}, {"q": 2, "y": 3}, {"a": 0, "b": "bb"}, {"a": "aa", "b": 7, "c": 8},
            {"s": 1, "t": 2}, "Sub"]
assert_eq(run(), expected)
assert_eq(log, ["iter", "keys", "a", "b", "iter", "iter", "keys", "a", "b"])
log.clear()

assert_eq([dict(Pairs([(1, 2)]), k=3), dict(Keyed(), **{"b": 0})], [{1: 2, "k": 3}, {"a": "aa", "b": 0}])
assert_eq(log, ["iter", "keys", "a", "b"])

def errors():
    d = {}
    out = []
    try: d.update(Gen(), z=1)
    except LookupError as e: out.append(e.args)
    try: dict(Gen(), z=1)
    except LookupError as e: out.append(e.args)
    out.append(d)
    return out

assert_eq(errors(), [("gen",), ("gen",), {"a": 1}])
