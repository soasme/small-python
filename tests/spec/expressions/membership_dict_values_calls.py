# spec: PLS-315 13.10, 26.4, 7.2.5
# description: in and not in of a dict's values view compare each value,
# in insertion order, with x by RichCompareBool, the value's Python __eq__
# or x's, which may loop, first; an identical value matches without a
# call, the result's truth is tested by its Python __bool__, and the
# search ends at the first match. Inside functions and comprehensions as
# at module level.
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
class K:
    def __init__(self, n): self.n = n
    def __eq__(self, other):
        spin(); log.append(("eq", self.n, getattr(other, "n", other)))
        return Truth(self.n == getattr(other, "n", other))
    __hash__ = object.__hash__

def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def main():
    d = {1: K(1), 2: K(2), 3: 7}
    check(lambda: 2 in d.values(), True, [("eq", 1, 2), ("bool", False), ("eq", 2, 2), ("bool", True)])
    check(lambda: 5 not in d.values(), True, [("eq", 1, 5), ("bool", False), ("eq", 2, 5), ("bool", False)])
    check(lambda: 7 in d.values(), True, [("eq", 1, 7), ("bool", False), ("eq", 2, 7), ("bool", False)])
    check(lambda: K(7) in {1: 7}.values(), True, [("eq", 7, 7), ("bool", True)])
    check(lambda: d[2] in d.values(), True, [("eq", 1, 2), ("bool", False)])
    check(lambda: [1 in {1: K(1)}.values() for _ in range(2)], [True, True], [("eq", 1, 1), ("bool", True)] * 2)
main()

check(lambda: 3 in {1: K(3)}.values(), True, [("eq", 3, 3), ("bool", True)])
