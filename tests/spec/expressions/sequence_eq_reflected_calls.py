# spec: PLS-315 25.5.3, 26.1.2, 7.2.5
# description: when an item's Python __eq__, compared by == or != of two
# lists, two tuples or two dicts, returns NotImplemented, the other item's
# Python __eq__, which may loop, is called with the operands reflected, and
# when it declines too, identity decides; the walk then goes on with the
# next pair or ends at an unequal one, and an error from the reflected
# method propagates. Inside functions, generators and nested sequences, as
# at module level.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class Declining:
    def __init__(self, tag): self.tag = tag
    def __eq__(self, other):
        spin(); log.append(self.tag + getattr(other, "tag", "?"))
        return NotImplemented
class K:
    def __init__(self, v, tag="k"): self.v, self.tag = v, tag
    def __eq__(self, other):
        spin(); log.append(self.tag + getattr(other, "tag", "?"))
        if self.v == 9: raise KeyError("reflected")
        return self.v == getattr(other, "v", self.v)

def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def main():
    d = Declining("s")
    check(lambda: [Declining("a"), 1] == [K(1, "b"), 1], True, ["ab", "ba"])
    check(lambda: (Declining("a"), K(2, "c")) == (K(1, "b"), K(3, "d")), False, ["ab", "ba", "cd"])
    check(lambda: [Declining("a")] != [K(1, "b")], False, ["ab", "ba"])
    # Both decline: identity decides, so equal only when the same.
    check(lambda: [Declining("a")] == [Declining("b")], False, ["ab", "ba"])
    check(lambda: [d, Declining("x")] == [d, Declining("y")], False, ["xy", "yx"])
    check(lambda: [Declining("a"), Declining("c")] == [Declining("b"), Declining("d")], False, ["ab", "ba"])
    check(lambda: [[Declining("a")], K(1, "c")] == [[K(1, "b")], K(1, "d")], True, ["ab", "ba", "cd"])
    check(lambda: {1: Declining("a"), 2: K(1, "c")} == {1: K(1, "b"), 2: K(1, "d")}, True, ["ab", "ba", "cd"])
    check(lambda: [Declining("a")] == [5], False, ["a?"])
    def gen():
        yield [Declining("a")] == [K(1, "b")]
    check(lambda: list(gen()), [True], ["ab", "ba"])
    log.clear()
    assert_raises(KeyError, lambda: [Declining("a")] == [K(9, "b")], message="'reflected'")
    assert_eq(log, ["ab", "ba"])
main()

check(lambda: [Declining("a"), 2] == [K(1, "b"), 2], True, ["ab", "ba"])
