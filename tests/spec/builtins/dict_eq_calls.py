# spec: PLS-315 26.1.2, 7.2.5
# description: == and != of two dicts of one length walk the first's
# entries while it has more, finding each key in the second and comparing
# the two values by RichCompareBool, the first's on the left, by Python
# __eq__ methods that may loop, with NotImplemented falling back to the
# reflected method and then identity; a missing key or an unequal value
# ends the walk, a comparison that empties the first dict ends it too, and
# an error propagates.
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
        if self.v == 9: raise KeyError("eq")
        if self.v == 7: emptied.clear()
        return isinstance(other, K) and other.v == self.v
class Declining:
    tag = "n"
    def __eq__(self, other): spin(); log.append("n"); return NotImplemented

def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

emptied = {}
def main():
    global emptied
    a = K(1, "a")
    check(lambda: {1: K(1, "a"), "s": 2, 3: K(2, "b")} == {"s": 2, 3: K(2, "c"), 1: K(1, "d")}, True, ["ad", "bc"])
    check(lambda: {1: K(1, "a")} != {1: K(2, "b")}, True, ["ab"])
    # Identical values match without a call.
    check(lambda: {1: a, 2: K(1, "x")} == {1: a, 2: K(1, "y")}, True, ["xy"])
    check(lambda: ({1: K(1, "a")} == {2: K(1, "b")}, {1: K(1, "a")} == {1: K(1, "b"), 2: 3}), (False, False), [])
    check(lambda: {1: K(1, "a"), 2: K(2, "b")} == {1: K(3, "c"), 2: K(2, "d")}, False, ["ac"])
    check(lambda: ({1: Declining()} == {1: K(1, "b")}, {1: K(1, "a")} == {1: Declining()}), (False, False), ["n", "bn", "an"])
    check(lambda: {1: Declining()} == {1: Declining()}, False, ["n", "n"])
    # Values in a list compare as the list does; keys whose lookup calls
    # Python compare as a lookup does.
    check(lambda: {1: K(1, "a"), 2: [K(3, "p")]} == {1: K(1, "b"), 2: [K(3, "q")]}, True, ["ab", "pq"])
    check(lambda: {K(1, "a"): K(1, "c")} == {K(1, "b"): K(1, "d")}, True, ["ba", "cd"])
    check(lambda: {1: 2, K(5, "e"): 1, 3: K(1, "f")} == {1: 2, K(5, "g"): 1, 3: K(1, "h")}, True, ["ge", "fh"])
    emptied = {1: K(7, "m"), 2: K(1, "a")}
    check(lambda: emptied == {1: K(7, "n"), 2: K(2, "b")}, True, ["mn"])
    check(lambda: [{1: K(1, "a")} == {1: K(1, "b")} == {1: K(1, "c")}], [True], ["ab", "bc"])
    def gen():
        yield {1: K(1, "a")} == {1: K(1, "b")}
    check(lambda: list(gen()), [True], ["ab"])
    def test():
        if {1: K(1, "a")} != {1: K(1, "b")}: return "unequal"
        return "equal"
    check(test, "equal", ["ab"])
main()

assert_raises(KeyError, lambda: {1: K(9)} == {1: K(1)}, message="'eq'")
