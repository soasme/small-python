# spec: PLS-315 19.3.34, 25.1.4, 7.2.5
# description: sorted() and list.sort() test the truth of each Python __lt__
# result, and of the __eq__ results by which tuple keys find their first
# unequal items, by the result's Python __bool__, or __len__ without one,
# which may loop; a true result orders the pair. A __bool__ that returns
# no bool raises TypeError. Keys a key function returns, a reversed sort,
# and sorts inside functions and generators, as at module level.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class Truth:
    def __init__(self, value): self.value = value
    def __bool__(self):
        spin(); log.append(("bool", self.value))
        return self.value
class Sized:
    def __init__(self, value): self.value = value
    def __len__(self):
        spin(); log.append(("len", self.value))
        return int(self.value)
class Ord:
    def __init__(self, n, kind=Truth): self.n, self.kind = n, kind
    def __lt__(self, other):
        spin(); log.append(("lt", self.n, other.n))
        return self.kind(self.n < other.n)
    def __eq__(self, other):
        spin(); log.append(("eq", self.n, other.n))
        return Truth(self.n == other.n)
    def __repr__(self): return "O%d" % self.n

def check(expression, value, calls):
    log.clear()
    assert_eq(repr(expression()), value)
    assert_eq(log, calls)

def main():
    check(lambda: sorted([Ord(3), Ord(1)]), "[O1, O3]", [("lt", 1, 3), ("bool", True)])
    check(lambda: sorted([Ord(3, Sized), Ord(1, Sized)]), "[O1, O3]", [("lt", 1, 3), ("len", True)])
    check(lambda: sorted([(Ord(1), 2), (Ord(1), 1)]), "[(O1, 1), (O1, 2)]", [("eq", 1, 1), ("bool", True)])
    items = [Ord(2), Ord(1)]
    check(lambda: (items.sort(), items), "(None, [O1, O2])", [("lt", 1, 2), ("bool", True)])
    check(lambda: sorted([1, 2], key=lambda i: Ord(-i)), "[2, 1]", [("lt", -2, -1), ("bool", True)])
    check(lambda: sorted([Ord(1), Ord(2)], reverse=True), "[O2, O1]", [("lt", 1, 2), ("bool", True)])
    def gen():
        yield sorted([Ord(2), Ord(1)])
    check(lambda: list(gen()), "[[O1, O2]]", [("lt", 1, 2), ("bool", True)])
    assert_raises(TypeError, lambda: sorted([Ord(1, lambda b: Truth(3)), Ord(2, lambda b: Truth(3))]), message="Truth.__bool__() must return a bool, not int")
main()

check(lambda: sorted([Ord(3), Ord(1)]), "[O1, O3]", [("lt", 1, 3), ("bool", True)])
