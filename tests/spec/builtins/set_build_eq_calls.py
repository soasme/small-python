# spec: PLS-315 26, 26.3.1, 26.3.2, 26.1.1
# description: set(), frozenset(), a set display's starred list, a set's
# update and dict.fromkeys find an element equal to a present one of the
# same hash by RichCompare of the present key with it, by Python __eq__
# methods that may loop: the present key's first, the element's on
# NotImplemented, a subclass's reflected method first, identity last; the
# present element is kept, a fromkeys key takes the value, a raising
# __eq__ propagates, and a comparison that empties the set adds the
# element.
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
    def __repr__(self): return self.tag
class Declining:
    def __init__(self, tag): self.tag = tag
    def __hash__(self): spin(); return 1
    def __eq__(self, other): spin(); log.append("d" + self.tag); return NotImplemented
    def __repr__(self): return self.tag
class Agreeing(K):
    def __eq__(self, other): spin(); log.append("sub"); return True
    __hash__ = K.__hash__
class Raising:
    tag = "r"
    def __hash__(self): spin(); return 1
    def __eq__(self, other): spin(); raise KeyError("eq")
class Emptying:
    tag = "e"
    def __init__(self, box): self.box = box
    def __hash__(self): spin(); return 1
    def __eq__(self, other): spin(); self.box.clear(); log.append("e"); return False

def check(make, value, calls):
    log.clear()
    result = make()
    assert_eq(sorted(map(repr, result.items() if isinstance(result, dict) else result)), value)
    assert_eq(log, calls)

def main():
    a, b, c = K(1, "a"), K(1, "b"), K(1, "c")
    check(lambda: set([a, b, K(2, "x"), c]), ["a", "x"], ["ab", "ac"])
    check(lambda: frozenset((a, Declining("n"), b)), ["a", "n"], ["an", "ab"])
    check(lambda: set([Declining("p"), Declining("q")]), ["p", "q"], ["dp", "dq"])
    check(lambda: {*[K(3, "x"), Agreeing(3, "y")]}, ["x"], ["sub"])
    check(lambda: dict.fromkeys([a, b], 5), ["(a, 5)"], ["ab"])
    check(lambda: dict.fromkeys([a, K(2, "x"), b]), ["(a, None)", "(x, None)"], ["ab"])
    present = {1, K(1, "m")}
    log.clear()
    present.update([K(1, "n")])
    assert_eq(len(present), 2)
    assert_eq(log, ["n?", "mn"])
    check(lambda: set([1, K(1, "o")]), ["1", "o"], ["o?"])
    def gen():
        log.append("y"); yield a
        log.append("y"); yield b
    check(lambda: set(gen()), ["a"], ["y", "y", "ab"])
main()

assert_raises(KeyError, lambda: set([Raising(), Raising()]), message="'eq'")
assert_raises(KeyError, lambda: dict.fromkeys((Raising(), Raising())), message="'eq'")
box = set()
log.clear()
box.update([Emptying(box), Emptying(box)])
assert_eq((len(box), log), (1, ["e"]))
