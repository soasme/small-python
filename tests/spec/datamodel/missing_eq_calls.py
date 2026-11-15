# spec: PLS-315 26.1.2, 7.3.2
# description: d[k] on an instance of a dict subclass with a Python
# __missing__ compares k with each stored key of its hash by the keys'
# Python __eq__, which may loop, and calls __missing__ with the instance
# and k only when none is equal; __missing__'s result is the subscript's
# value, and an exception of __eq__ or __missing__ propagates. A key's
# Python __hash__ is called once first. Plain and augmented subscripts,
# inside functions as at module level.
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
        if other.n == -1: raise ValueError("eq")
        return self.n == other.n

class Missing(dict):
    def __missing__(self, key):
        for _ in range(2): pass
        log.append(("missing", key.n))
        if key.n == -2: raise LookupError("missing")
        return key.n * 10

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def items():
    d = Missing({Key(1): 1, Key(2): 2})
    del log[:]
    out = [d[Key(2)], d[Key(3)], error(lambda: d[Key(-1)]), error(lambda: d[Key(-2)])]
    k = Key(4)
    d[k] += 1
    out += [d[k], len(d), list(log)]
    return out

expected = [2, 30, ("ValueError", "eq"), ("LookupError", "missing"), 41, 3,
            [("hash", 2), ("eq", 1, 2), ("eq", 2, 2), ("hash", 3), ("eq", 1, 3), ("eq", 2, 3), ("missing", 3),
             ("hash", -1), ("eq", 1, -1), ("hash", -2), ("eq", 1, -2), ("eq", 2, -2), ("missing", -2),
             ("hash", 4), ("eq", 1, 4), ("eq", 2, 4), ("missing", 4), ("hash", 4), ("eq", 1, 4), ("eq", 2, 4),
             ("hash", 4), ("eq", 1, 4), ("eq", 2, 4)]]

def main():
    return items()

assert_eq(main(), expected)
assert_eq(items(), expected)
