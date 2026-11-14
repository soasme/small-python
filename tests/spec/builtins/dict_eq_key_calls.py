# spec: PLS-315 26.1.2, 7.2.5
# description: == and != of two dicts of one length find each key of the
# first in the second by its lookup, calling a Python __eq__ of a key of
# the same hash, which may loop, before comparing that entry's values,
# which may call their own; a key's NotImplemented falls back to the
# reflected method and then identity, its error propagates, tuple keys
# compare their items, colliding keys are tried in turn, and a key's
# __eq__ that empties the first dict ends the walk; in a chain, in a
# generator, inside functions as at module level.
from harness import *

log = []

def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class K:
    def __init__(self, v, h=None): self.v, self.h = v, h
    def __hash__(self): return hash(self.v if self.h is None else self.h)
    def __eq__(self, other):
        spin(); log.append(("k", self.v, getattr(other, "v", other)))
        if self.v == "err": raise KeyError("k")
        if self.v == "ni": return NotImplemented
        return isinstance(other, K) and self.v == other.v

class V:
    def __init__(self, v): self.v = v
    def __eq__(self, other):
        spin(); log.append(("v", self.v, getattr(other, "v", other)))
        if self.v == "err": raise ValueError("v")
        return isinstance(other, V) and self.v == other.v

class Emptying:
    def __init__(self, d): self.d = d
    def __hash__(self): return 1
    def __eq__(self, other):
        spin(); log.append("empty"); self.d.clear(); return True

def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def main():
    check(lambda: {K(1): 1, K(2): 2} == {K(1): 1, K(2): 2}, True, [("k", 1, 1), ("k", 2, 2)])
    check(lambda: ({K(1): 1} != {K(1): 1}, {K(1): 1} == {K(2): 1}, {K(1): 1} == {K(1): 2}), (False, False, False),
          [("k", 1, 1), ("k", 1, 1)])
    check(lambda: {K(1): V(1), "a": V(2)} == {"a": V(2), K(1): V(1)}, True, [("k", 1, 1), ("v", 1, 1), ("v", 2, 2)])
    check(lambda: {K(1): V(1), K(2): 2} == {K(1): V(3), K(2): 2}, False, [("k", 1, 1), ("v", 1, 3)])
    check(lambda: ({K(1): [V(1)]} == {K(1): [V(1)]}, {K(1): (V(1), 2)} == {K(1): (V(1), 3)}), (True, False),
          [("k", 1, 1), ("v", 1, 1), ("k", 1, 1), ("v", 1, 1)])
    check(lambda: {(K(1), 2): 1} == {(K(1), 2): 1}, True, [("k", 1, 1)])
    check(lambda: {K(1, 5): 1, K(2, 5): 2} == {K(2, 5): 2, K(1, 5): 1}, True,
          [("k", 1, 2), ("k", 2, 1), ("k", 2, 1), ("k", 1, 1), ("k", 2, 2)])
    check(lambda: {K("ni"): 1} == {K("ni"): 1}, False, [("k", "ni", "ni"), ("k", "ni", "ni")])
    k = K(1)
    check(lambda: {k: V(1)} == {k: V(1)}, True, [("v", 1, 1)])
    check(lambda: error(lambda: {K("err"): 1} == {K("err"): 1}), ("KeyError", "'k'"), [("k", "err", "err")])
    check(lambda: error(lambda: {K(1): V("err")} == {K(1): V(2)}), ("ValueError", "v"), [("k", 1, 1), ("v", "err", 2)])
    first = {}
    first[Emptying(first)] = 1
    first[K(9)] = 2
    check(lambda: first == {Emptying(first): 1, K(9): 2}, True, ["empty"])
    check(lambda: {K(1): 1} == {K(1): 1} == {K(1): 1}, True, [("k", 1, 1), ("k", 1, 1)])
    def gen():
        yield {K(3): V(3)} == {K(3): V(3)}
    check(lambda: list(gen()), [True], [("k", 3, 3), ("v", 3, 3)])

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

main()
main()
log.clear()
assert_eq([{K(1): V(1)} == {K(1): V(1)}, {K(2): 1} != {K(2): 1}], [True, False])
assert_eq(log, [("k", 1, 1), ("v", 1, 1), ("k", 2, 2)])
assert_raises(KeyError, lambda: {K("err"): 1} == {K("err"): 1}, message="'k'")
