# spec: PLS-315 26.1.1, 26.1.3
# description: dict(x) and d.update(x) of an instance that has no keys
# attribute take the pairs its Python __iter__, which may loop, gives,
# in order, a later key's value replacing an earlier one's; an instance
# with keys, from its namespace, its class or __getattr__, is a mapping
# instead. An element that is not a pair of two items, or not iterable,
# is an error whose message or note names its index, and an exception from __iter__ or from
# the pairs' iteration propagates, the dict keeping the pairs before
# it. Inside functions as at module level.
from harness import *

log = []

class Pairs:
    def __init__(self, items): self.items = items
    def __iter__(self):
        for _ in (): pass
        log.append("iter")
        if self.items == "raise": raise LookupError("iter")
        return iter(self.items)

class Gen:
    def __iter__(self):
        for _ in (): pass
        yield "a", 1
        yield ["b", 2]
        yield "cd"
        raise LookupError("gen")

class Keyed(Pairs):
    def keys(self):
        for _ in (): pass
        log.append("keys")
        return ["k"]
    def __getitem__(self, k):
        for _ in (): pass
        return k + "!"

class Fallback(Pairs):
    def __getattr__(self, name):
        for _ in (): pass
        log.append(name)
        if name == "keys": return lambda: ["f"]
        raise AttributeError(name)
    def __getitem__(self, k): return k * 2

def failure(f):
    try: f()
    except Exception as e: return (type(e).__name__, str(e)) + tuple(getattr(e, "__notes__", ()))

def run():
    own = Pairs([("o", 1)]); own.keys = lambda: ["n"]
    d = {"x": 0}
    d.update(Pairs([("x", 1), ("y", 2), ("x", 3)]))
    return [dict(Pairs([("a", 1), ["b", 2], "cd"])), d, dict(Keyed([("p", 1)])), dict(Fallback([("p", 1)])),
            failure(lambda: dict(own))]

expected = [{"a": 1, "b": 2, "c": "d"}, {"x": 3, "y": 2}, {"k": "k!"}, {"f": "ff"},
            ("TypeError", "'Pairs' object is not subscriptable")]
assert_eq(run(), expected)
assert_eq(log, ["iter", "iter", "keys", "keys", "keys"])
log.clear()

assert_eq([dict(Pairs([(1, 2)])), dict(Keyed([]))], [{1: 2}, {"k": "k!"}])
assert_eq(log, ["iter", "keys"])
log.clear()

def errors():
    d = {}
    out = [failure(lambda: dict(Pairs([("a", 1), (1, 2, 3)]))), failure(lambda: dict(Pairs([("a", 1), 5]))),
           failure(lambda: dict(Pairs("raise"))), failure(lambda: d.update(Gen())), d]
    return out

assert_eq(errors(), [("ValueError", "dictionary update sequence element #1 has length 3; 2 is required"),
                     ("TypeError", "object is not iterable", "Cannot convert dictionary update sequence element #1 to a sequence"),
                     ("LookupError", "iter"), ("LookupError", "gen"), {"a": 1, "b": 2, "c": "d"}])
