# spec: PLS-315 25.2, 7.5.7, 26.1.2, 26.1.3, 26.3.2
# description: a tuple key of a dict or set display, subscript, store,
# deletion, augmented assignment, in test or get, setdefault, pop, add,
# discard or remove calls Hash of its items in order, nested tuples
# depth first, each by a Python __hash__ that may loop; the tuple keeps
# its hash, so hashing it again calls none, while an item's error or
# wrong result stops the hash, keeps none, and propagates.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class K:
    def __init__(self, v): self.v = v
    def __hash__(self): spin(); log.append("h%d" % self.v); return self.v
    def __eq__(self, other): return isinstance(other, K) and other.v == self.v

def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def main():
    a, b, c = K(1), K(2), K(3)
    check(lambda: {(a, 1): "x", (1, (b, a)): "y"}, {(K(1), 1): "x", (1, (K(2), K(1))): "y"}, ["h1", "h2", "h1"])
    d = {(a, 1): "x", (1, (b, a)): "y"}
    check(lambda: (d[(a, 1)], d[1, (b, a)]), ("x", "y"), ["h1", "h2", "h1"])
    key = (b, a)
    check(lambda: (hash(key) == hash((2, 1)), d[1, key], {key}), (True, "y", {(K(2), K(1))}), ["h2", "h1"])
    check(lambda: d[(K(1), 1)], "x", ["h1"])
    check(lambda: ((a, 1) in d, (c,) in d, (c,) in {1}), (True, False, False), ["h1", "h3", "h3"])
    def store():
        d[(c, c)] = 3
        d[(b,)] = 4
        del d[(b,)]
        return len(d)
    check(store, 3, ["h3", "h3", "h2", "h2"])
    check(lambda: (d.get((K(1), 1)), d.setdefault((K(4),), 5), d.pop((K(3), c))), ("x", 5, 3), ["h1", "h4", "h3", "h3"])
    s = {(a,), (b, 2)}
    def sets():
        s.add((K(1), K(2)))
        s.discard((K(2), 2))
        s.remove((K(1),))
        return len(s)
    check(sets, 1, ["h1", "h2", "h2", "h1"])
    def augmented():
        key = (K(7),)
        d[key] = 0
        d[key] += 1
        return d[(K(7),)]
    check(augmented, 1, ["h7", "h7"])
    def gen():
        yield {(a,): 1}[(K(1),)]
        yield (K(2), (K(3),)) in d
    check(lambda: list(gen()), [1, False], ["h1", "h1", "h2", "h3"])
main()

# An item's error, or a hash that is not an int, stops the tuple's hash
# and keeps none.
class Raising:
    def __hash__(self): spin(); log.append("r"); raise ValueError("r")
class Wrong:
    def __hash__(self): spin(); return "w"
a = K(1)
log.clear()
bad = (a, Raising(), K(2))
assert_raises(ValueError, lambda: {bad: 1}, message="r")
assert_raises(ValueError, lambda: {}.get(bad), message="r")
assert_eq(log, ["h1", "r", "h1", "r"])
assert_raises(TypeError, lambda: {(1, (Wrong(),)): 1},
              message="cannot use 'tuple' as a dict key (__hash__ method should return an integer)")
log.clear()
assert_raises(TypeError, lambda: {(a, []): 1}, message="cannot use 'tuple' as a dict key (unhashable type: 'list')")
assert_raises(TypeError, lambda: (a, []) in {1}, message="cannot use 'tuple' as a set element (unhashable type: 'list')")
assert_eq(log, ["h1", "h1"])
# An unhashable item before one with a Python __hash__ stops the hash
# there, and a __hash__ that cannot take its item raises its TypeError.
log.clear()
assert_raises(TypeError, lambda: {([], a): 1}, message="cannot use 'tuple' as a dict key (unhashable type: 'list')")
assert_eq(log, [])
class Unbound:
    def __hash__(): spin(); return 1
assert_raises(TypeError, lambda: {(Unbound(),): 1}, message="cannot use 'tuple' as a dict key (Unbound.__hash__() takes 0 positional arguments but 1 was given)")
assert_raises(TypeError, lambda: {}.get((a, Unbound())), message="cannot use 'tuple' as a dict key (Unbound.__hash__() takes 0 positional arguments but 1 was given)")
assert_eq(log, ["h1"])
