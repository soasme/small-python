# spec: PLS-315 19.3.26, 7.2.4, 7.2.5
# description: min() and max() of a list or of several arguments compare
# each item with the best so far by the item's Python __lt__ or __gt__,
# which may loop: when it returns NotImplemented the best's reflected
# method is called, and when both decline TypeError names the operator;
# the truth of a result is tested by its Python __bool__, which may loop,
# a true one making the item the best. A __bool__ that returns no bool
# raises TypeError. Inside functions and generators as at module level.
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
class Ord:
    def __init__(self, n, result=None): self.n, self.result = n, result
    def __lt__(self, other):
        spin(); log.append(("lt", self.n, other.n))
        return Truth(self.n < other.n) if self.result is None else self.result
    def __gt__(self, other):
        spin(); log.append(("gt", self.n, other.n))
        return Truth(self.n > other.n)
    def __repr__(self): return "O%d" % self.n
class Declining:
    n = 0
    def __lt__(self, other): spin(); log.append("dlt"); return NotImplemented
    def __gt__(self, other): spin(); log.append("dgt"); return NotImplemented
    def __repr__(self): return "D"

def check(expression, value, calls):
    log.clear()
    assert_eq(repr(expression()), value)
    assert_eq(log, calls)

def main():
    check(lambda: min([Ord(3), Ord(1), Ord(2)]), "O1", [("lt", 1, 3), ("bool", True), ("lt", 2, 1), ("bool", False)])
    check(lambda: max(Ord(3), Ord(5), Ord(4)), "O5", [("gt", 5, 3), ("bool", True), ("gt", 4, 5), ("bool", False)])
    check(lambda: min([Ord(3, NotImplemented), Ord(1, NotImplemented)]), "O1", [("lt", 1, 3), ("gt", 3, 1), ("bool", True)])
    check(lambda: (min([Declining(), Ord(1)]), max([Ord(1), Declining()])), "(D, O1)",
          [("lt", 1, 0), ("bool", False), "dgt", ("lt", 1, 0), ("bool", False)])
    def gen():
        yield min(Ord(2), Ord(1))
    check(lambda: list(gen()), "[O1]", [("lt", 1, 2), ("bool", True)])
    log.clear()
    assert_raises(TypeError, lambda: min([Declining(), Declining()]), message="'<' not supported between instances of 'Declining' and 'Declining'")
    assert_eq(log, ["dlt", "dgt"])
    assert_raises(TypeError, lambda: min([Ord(1), Ord(2, Truth(3))]), message="Truth.__bool__() must return a bool, not int")
main()

check(lambda: min([Ord(2), Ord(1)]), "O1", [("lt", 1, 2), ("bool", True)])
