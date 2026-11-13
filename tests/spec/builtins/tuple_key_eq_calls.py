# spec: PLS-315 26, 25.5.3, 26.1.2, 26.3.2
# description: a dict or set finds a tuple key equal to a stored tuple of
# the same hash by RichCompare of the stored key with it, which compares
# their items in order, nested tuples depth first, by Python __eq__
# methods that may loop, the stored item's first; a display, subscript,
# store, deletion, in test, get, setdefault, pop, add, discard or remove,
# and a set's comparison and union, do so whether or not the key's hash
# was just computed, and an error propagates.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class K:
    def __init__(self, v, tag="k"): self.v, self.tag = v, tag
    def __hash__(self): return self.v
    def __eq__(self, other):
        spin(); log.append(self.tag + getattr(other, "tag", "?"))
        return isinstance(other, K) and other.v == self.v
class Declining:
    tag = "n"
    def __hash__(self): return 1
    def __eq__(self, other): spin(); log.append("n"); return NotImplemented

def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def main():
    a = K(1, "a")
    d = {(a, 1): "x", (1, (K(2, "c"), a)): "y"}
    check(lambda: d[(K(1, "b"), 1)], "x", ["ab"])
    check(lambda: d[1, (K(2, "e"), K(1, "f"))], "y", ["ce", "af"])
    check(lambda: ((K(1, "b"), 2) in d, d.get((K(1, "g"), 1))), (False, "x"), ["ag"])
    key = (K(1, "r"), 1)
    check(lambda: (d[key], d[key], key in d), ("x", "x", True), ["ar", "ar", "ar"])
    def store():
        d[(K(1, "s"), 1)] = "z"
        del d[(K(1, "t"), 1)]
        return len(d)
    check(store, 1, ["as", "at"])
    check(lambda: [(k[0].tag, v) for k, v in {(K(1, "p"),): 1, (K(1, "q"),): 2}.items()], [("p", 2)], ["pq"])
    s = {(a,)}
    def add():
        s.add((K(1, "u"),))
        return len(s)
    check(add, 1, ["au"])
    check(lambda: ({(a,)} == {(K(1, "w"),)}, {(a,)} | {(K(1, "x"),)}), (True, {(a,)}), ["wa", "ax"])
    # A stored item's NotImplemented gives the key's item its reflected call.
    check(lambda: {(Declining(),): 1}.get((K(1, "m"),), "-"), "-", ["n", "mn"])
    def gen():
        yield (K(1, "h"),) in s
    check(lambda: list(gen()), [True], ["ah"])
    # A kept hash leaves the items' comparison to get, setdefault, pop,
    # add, discard and remove.
    kept = (K(1, "j"), 1)
    hash(kept)
    e = {(a, 1): "x"}
    check(lambda: (e.get(kept), e.setdefault(kept, 0), e.pop(kept), e), ("x", "x", "x", {}), ["aj", "aj", "aj"])
    one = (K(1, "o"),)
    hash(one)
    def methods():
        t = {(a,)}
        t.add(one); t.discard(one); t.add(one); t.remove(one)
        return len(t)
    check(methods, 0, ["ao", "ao"])
main()

class Raising:
    def __hash__(self): return 1
    def __eq__(self, other): spin(); raise KeyError("eq")
assert_raises(KeyError, lambda: {(Raising(),): 1}[(Raising(),)], message="'eq'")
assert_raises(KeyError, lambda: {(1, (Raising(),))}.add((1, (Raising(),))), message="'eq'")
