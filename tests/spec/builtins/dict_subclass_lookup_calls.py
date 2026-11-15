# spec: PLS-315 26, 26.1.2
# description: d[k], k in d, k not in d, d.get(k), d.setdefault(k) and
# d.pop(k) on an instance of a dict subclass that keeps dict's methods
# hash the key once and compare it with each stored key of that hash by
# the Python __eq__, which may loop, in insertion order until one
# matches: an absent key's subscript raises KeyError with the key, and an
# exception of __eq__ propagates from the lookup, leaving the dict as it
# was. Inside functions as at module level.
from harness import *

log = []

class Key:
    def __init__(self, n): self.n = n
    def __hash__(self):
        log.append(("hash", self.n))
        return 1
    def __eq__(self, other):
        for _ in range(2): pass
        log.append(("eq", self.n, other.n))
        if other.n < 0: raise ValueError(other.n)
        return other.n == self.n

class Sub(dict): pass

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, e.args[0] if type(e.args[0]) is int else e.args[0].n

def lookups():
    d = Sub({Key(1): "one", Key(2): "two"})
    del log[:]
    out = [d[Key(2)], Key(2) in d, Key(3) in d, Key(3) not in d, d.get(Key(1)), d.get(Key(3), "no"),
           d.setdefault(Key(4), "four"), d.pop(Key(2)), len(d)]
    out += [error(lambda: d[Key(5)]), error(lambda: d[Key(-1)]), error(lambda: Key(-2) in d), len(d), list(log)]
    return out

expected = ["two", True, False, True, "one", "no", "four", "two", 2, ("KeyError", 5), ("ValueError", -1), ("ValueError", -2), 2,
            [("hash", 2), ("eq", 1, 2), ("eq", 2, 2), ("hash", 2), ("eq", 1, 2), ("eq", 2, 2), ("hash", 3), ("eq", 1, 3), ("eq", 2, 3),
             ("hash", 3), ("eq", 1, 3), ("eq", 2, 3), ("hash", 1), ("eq", 1, 1), ("hash", 3), ("eq", 1, 3), ("eq", 2, 3),
             ("hash", 4), ("eq", 1, 4), ("eq", 2, 4), ("hash", 2), ("eq", 1, 2), ("eq", 2, 2),
             ("hash", 5), ("eq", 1, 5), ("eq", 4, 5), ("hash", -1), ("eq", 1, -1), ("hash", -2), ("eq", 1, -2)]]

def main():
    return lookups()

assert_eq(main(), expected)
assert_eq(lookups(), expected)
