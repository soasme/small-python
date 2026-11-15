# spec: PLS-315 26.1.2, 10.5
# description: A dict subclass's subscript of an absent key calls its
# Python __missing__ with the key, also for tuple keys, nested or not,
# and their result is the subscript's value; a present tuple key gives
# its stored value without the call, a key equal to a stored one by a
# Python __eq__ finds it, and an exception from __missing__ propagates.
# Inside functions as at module level.
from harness import *

log = []

class D(dict):
    def __missing__(self, key):
        for _ in (): pass
        log.append(key)
        if key == ("bad",): raise KeyError(key)
        return len(key)

class E:
    def __init__(self, v): self.v = v
    def __hash__(self): return 7
    def __eq__(self, other):
        log.append("eq")
        return isinstance(other, E) and self.v == other.v

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, e.args

def results():
    del log[:]
    d = D({(1, 2): "stored", (E(1),): "e"})
    out = [d[(1, 2)], d[(1, 2, 3)], d[((1,), "a")], d[()], d["abc"], d[(E(1),)], d[(3,)]]
    out += [error(lambda: d[("bad",)]), log]
    return out

expected = ["stored", 3, 2, 0, 3, "e", 1, ("KeyError", (("bad",),)),
            [(1, 2, 3), ((1,), "a"), (), "abc", "eq", (3,), ("bad",)]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
