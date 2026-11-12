# spec: PLS-315 27.1.6, 27.1.5, 7.5.1
# description: map() of str, repr, format, hash, len or abs calls each
# item's Python method as it takes the item, and filter() of None or bool
# takes each item's truth by its __bool__ or __len__, from a list, a
# tuple, an iterator or a generator, in a loop or a consumer; results are
# checked as the direct call checks them, and errors propagate.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class K:
    def __init__(self, v): self.v = v
    def __str__(self): spin(); log.append("s%d" % self.v); return "k%d" % self.v
    def __repr__(self): spin(); log.append("r%d" % self.v); return "K%d" % self.v
    def __bool__(self): spin(); log.append("b%d" % self.v); return self.v > 0
    def __format__(self, spec): spin(); log.append("f"); return "F" + spec
    def __hash__(self): spin(); log.append("h"); return self.v
    def __len__(self): return 9
    def __abs__(self): spin(); return "abs"
class Sized:
    def __init__(self, n): self.n = n
    def __len__(self): spin(); log.append("l%d" % self.n); return self.n
def gen(*items):
    for item in items: yield item

a, b, z = K(1), K(2), K(0)
def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def main():
    check(lambda: list(map(str, [a, b])), ["k1", "k2"], ["s1", "s2"])
    check(lambda: list(map(repr, (a, 3, b))), ["K1", "3", "K2"], ["r1", "r2"])
    check(lambda: list(map(str, iter([a, "x"]))), ["k1", "x"], ["s1"])
    check(lambda: list(map(str, gen(b, a))), ["k2", "k1"], ["s2", "s1"])
    check(lambda: list(map(format, [a])), ["F"], ["f"])
    check(lambda: list(map(hash, [a, b])), [1, 2], ["h", "h"])
    check(lambda: list(map(len, [a, [1]])), [9, 1], [])
    check(lambda: list(map(abs, [a, -1])), ["abs", 1], [])
    check(lambda: ",".join(map(str, [a, b])), "k1,k2", ["s1", "s2"])
    check(lambda: sorted(map(str, [b, a])), ["k1", "k2"], ["s2", "s1"])
    check(lambda: list(map(pow, [2, 3], [3, 2])), [8, 9], [])
    check(lambda: [v.v for v in filter(None, [a, z, 0, b])], [1, 2], ["b1", "b0", "b2"])
    check(lambda: [v.n for v in filter(None, (Sized(0), Sized(3)))], [3], ["l0", "l3"])
    check(lambda: [v.v for v in filter(bool, iter([z, a]))], [1], ["b0", "b1"])
    check(lambda: [v.v for v in filter(None, gen(a, z))], [1], ["b1", "b0"])
    def loop():
        seen = []
        for text in map(repr, [a, b]): seen.append(text)
        for item in filter(None, [z, b]): seen.append(item.v)
        return seen
    check(loop, ["K1", "K2", 2], ["r1", "r2", "b0", "b2"])
main()

# A result the direct call would refuse, or a raising method, stops there;
# a StopIteration from the method ends the map.
class WrongStr:
    def __str__(self): spin(); return 1
class WrongBool:
    def __bool__(self): spin(); return 1
class Negative:
    def __len__(self): spin(); return -1
class Stop:
    def __str__(self): spin(); raise StopIteration
class Raising:
    def __repr__(self): spin(); raise KeyError("k")
assert_raises(TypeError, lambda: list(map(str, [WrongStr()])), message="WrongStr.__str__() must return a str, not int")
assert_raises(TypeError, lambda: [x for x in map(str, [WrongStr()])], message="WrongStr.__str__() must return a str, not int")
assert_raises(TypeError, lambda: list(filter(None, [WrongBool()])), message="WrongBool.__bool__() must return a bool, not int")
assert_raises(ValueError, lambda: list(filter(bool, [Negative()])), message="__len__() should return >= 0")
assert_raises(KeyError, lambda: list(map(repr, [a, Raising()])), message="'k'")
log.clear()
assert_eq(list(map(str, [a, Stop(), b])), ["k1"])
assert_eq(log, ["s1"])
