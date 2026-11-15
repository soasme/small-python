# spec: PLS-315 26, 26.1.2
# description: d[k], d[k] = v and del d[k] on an instance of a dict
# subclass that keeps dict's __getitem__, __setitem__ and __delitem__ hash
# the key once by its Python __hash__, which may loop, before the lookup,
# store or deletion, an absent key's lookup calling __missing__; its
# exception propagates and leaves the dict as it was, and an absent key's
# deletion raises KeyError after hashing it. Plain, augmented and target
# list stores, inside functions as at module level.
from harness import *

log = []

class Key:
    def __init__(self, n): self.n = n
    def __hash__(self):
        for _ in range(2): pass
        log.append(("hash", self.n))
        if self.n < 0: raise ValueError(self.n)
        return self.n
    def __eq__(self, other): return isinstance(other, Key) and other.n == self.n
    def __repr__(self): return "K%d" % self.n

class Sub(dict):
    def __missing__(self, key): return 0

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def stores():
    del log[:]
    d = Sub()
    a, b = Key(1), Key(2)
    d[a] = "one"
    d[b], d[Key(3)] = "two", "three"
    d[a] += "!"
    out = [sorted(d.values()), d[a], d[Key(5)]]
    del d[b]
    def bad_store(): d[Key(-1)] = 0
    def bad_delete(): del d[Key(-2)]
    def absent(): del d[Key(4)]
    out += [error(bad_store), error(bad_delete), error(absent), sorted(d.values()), list(log)]
    return out

expected = [["one!", "three", "two"], "one!", 0, ("ValueError", "-1"), ("ValueError", "-2"), ("KeyError", "K4"), ["one!", "three"],
            [("hash", 1), ("hash", 2), ("hash", 3), ("hash", 1), ("hash", 1), ("hash", 1), ("hash", 5), ("hash", 2), ("hash", -1), ("hash", -2),
             ("hash", 4)]]

def main():
    return stores()

assert_eq(main(), expected)
assert_eq(stores(), expected)
