# spec: PLS-315 26.1.3, 26.3.2, 26
# description: a dict's get, setdefault and pop, and a set's add, discard
# and remove, find a key equal to a present one of the same hash by
# RichCompare of the present key with it, by Python __eq__ methods that may
# loop: the present key's first, the argument's on NotImplemented, a
# subclass's reflected method first; an absent key is inserted or missed as
# the method says, an error propagates, and a comparison that empties the
# container leaves the key absent.
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
        return other.v == self.v if isinstance(other, K) else NotImplemented
    def __repr__(self): return self.tag
class Declining:
    def __init__(self, tag): self.tag = tag
    def __hash__(self): spin(); return 1
    def __eq__(self, other): spin(); log.append("d" + self.tag); return NotImplemented
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

def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def main():
    a = K(1, "a")
    d = {a: "x", K(2, "t"): "y"}
    check(lambda: d.get(K(1, "b")), "x", ["ab"])
    check(lambda: d.get(K(3, "c"), "no"), "no", [])
    check(lambda: d.get(Declining("n"), "no"), "no", ["an", "dn"])
    check(lambda: d.get(Agreeing(2, "s")), "y", ["sub"])
    check(lambda: d.setdefault(K(1, "b"), "z"), "x", ["ab"])
    check(lambda: d.setdefault(Declining("m"), "z"), "z", ["am", "dm"])
    assert_eq(len(d), 3)
    check(lambda: d.pop(K(1, "b")), "x", ["ab"])
    check(lambda: d.pop(K(2, "c"), "gone"), "y", ["tc"])
    check(lambda: d.pop(K(1, "b"), "gone"), "gone", ["dm", "bm"])
    assert_eq(len(d), 1)
    s = {a, 7}
    check(lambda: s.add(K(1, "b")), None, ["ab"])
    check(lambda: (s.discard(K(1, "c")), len(s)), (None, 1), ["ac"])
    s.add(a)
    check(lambda: set.add(s, K(1, "u")), None, ["au"])
    check(lambda: (s.remove(K(1, "r")), s), (None, {7}), ["ar"])
    s.add(a)
    log.clear()
    try:
        s.remove(Declining("q"))
    except KeyError as e:
        assert_eq(e.args[0].tag, "q")
    assert_eq(log, ["aq", "dq"])
    def gen():
        yield d.get(K(1, "g"), "-")
        yield s.discard(K(1, "h"))
    check(lambda: list(gen()), ["-", None], ["dm", "gm", "ah"])
main()

# An error stops the method; a comparison that empties the container
# leaves the key absent.
assert_raises(KeyError, lambda: {Raising(): 1}.get(Raising()), message="'eq'")
assert_raises(KeyError, lambda: {Raising()}.add(Raising()), message="'eq'")
box = {}
box[Emptying(box)] = 1
log.clear()
assert_eq((box.setdefault(Emptying(box), 2), len(box), log), (2, 1, ["e"]))
items = set()
items.add(Emptying(items))
log.clear()
assert_raises(KeyError, lambda: items.remove(Emptying(items)))
assert_eq((len(items), log), (0, ["e"]))
