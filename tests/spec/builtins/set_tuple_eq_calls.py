# spec: PLS-315 26.3.1, 26.3.2, 26.1.1, 26, 25.5.3
# description: set(), frozenset(), a set's update, a set display's starred
# list and dict.fromkeys find a tuple element equal to a stored tuple of
# the same hash by RichCompare of the stored tuple with it, comparing
# their items in order, nested tuples depth first, by Python __eq__
# methods that may loop, the stored item's first; the stored tuple is
# kept, and an error stops the build.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class K:
    def __init__(self, v, tag="k"): self.v, self.tag = v, tag
    def __hash__(self): spin(); return self.v
    def __eq__(self, other):
        spin(); log.append(self.tag + getattr(other, "tag", "?"))
        return isinstance(other, K) and other.v == self.v

def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def tags(items):
    return sorted(t[0].tag if isinstance(t[0], K) else t[1][0].tag for t in items)

def main():
    check(lambda: tags(set([(K(1, "a"),), (K(1, "b"),)])), ["a"], ["ab"])
    check(lambda: tags(frozenset([(2, (K(3, "c"),)), (2, (K(3, "d"),))])), ["c"], ["cd"])
    check(lambda: [(k[0].tag, v) for k, v in dict.fromkeys([(K(1, "e"), 1), (K(1, "f"), 1)], 0).items()], [("e", 0)], ["ef"])
    def update():
        s = {(K(4, "g"),)}
        s.update([(K(4, "h"),), (K(5, "i"),)])
        return tags(s)
    check(update, ["g", "i"], ["gh"])
    check(lambda: tags({*[(K(1, "j"), 2), (K(1, "k"), 2)]}), ["j"], ["jk"])
    # Unequal items keep both tuples.
    check(lambda: len(set([(K(1, "l"), 1), (K(1, "m"), 2)])), 2, [])
    def gen():
        yield len(set([(K(6, "n"),), (K(6, "o"),)]))
    check(lambda: list(gen()), [1], ["no"])
main()

class Raising:
    def __hash__(self): spin(); return 1
    def __eq__(self, other): spin(); raise KeyError("eq")
assert_raises(KeyError, lambda: set([(Raising(),), (Raising(),)]), message="'eq'")
assert_raises(KeyError, lambda: dict.fromkeys([(1, (Raising(),)), (1, (Raising(),))]), message="'eq'")
