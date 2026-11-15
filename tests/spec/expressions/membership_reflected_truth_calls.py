# spec: PLS-315 13.10, 25.5.4, 7.2.5, 7.2.4
# description: in and not in of a list, a tuple or a list iterator, and a
# list's index, count and remove, compare each item with x by
# RichCompareBool: when the item's Python __eq__ returns NotImplemented,
# x's, which may loop, is called reflected, and when both decline,
# identity decides; the truth of a result is tested by its Python
# __bool__, or __len__ without one, which may loop. A true result ends the
# search, a __bool__ that returns no bool raises TypeError, and errors
# propagate. Inside functions and generators as at module level.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class Truth:
    def __init__(self, value): self.value = value
    def __bool__(self):
        spin(); log.append(("bool", self.value))
        if self.value == "bad": raise ValueError("bool")
        return self.value
class Sized:
    def __init__(self, n): self.n = n
    def __len__(self): spin(); log.append(("len", self.n)); return self.n
class Odd:
    def __init__(self, result): self.result = result
    def __eq__(self, other): spin(); log.append("odd"); return self.result
class Declining:
    def __init__(self, tag): self.tag = tag
    def __eq__(self, other): spin(); log.append(self.tag); return NotImplemented
class K:
    def __init__(self, v): self.v = v
    def __eq__(self, other): spin(); log.append("k"); return self.v

def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def main():
    check(lambda: 1 in [Odd(Truth(False)), Odd(Truth(True)), 3], True, ["odd", ("bool", False), "odd", ("bool", True)])
    check(lambda: 1 not in (Odd(Sized(0)), Odd(Sized(2))), False, ["odd", ("len", 0), "odd", ("len", 2)])
    check(lambda: Declining("x") in [Declining("a"), K(True)], True, ["a", "x", "k"])
    check(lambda: Declining("x") in [Declining("a")], False, ["a", "x"])
    check(lambda: (d := Declining("x")) in [Declining("a"), d], True, ["a", "x"])
    check(lambda: K(Truth(True)) in [Declining("a")], True, ["a", "k", ("bool", True)])
    it = iter([Odd(Truth(False)), Odd(Truth(True)), 5])
    check(lambda: (1 in it, list(it)), (True, [5]), ["odd", ("bool", False), "odd", ("bool", True)])
    items = [Odd(Truth(False)), Declining("a"), Odd(Sized(1))]
    check(lambda: items.index(1), 2, ["odd", ("bool", False), "a", "odd", ("len", 1)])
    check(lambda: items.count(1), 1, ["odd", ("bool", False), "a", "odd", ("len", 1)])
    check(lambda: (items.remove(1), len(items)), (None, 2), ["odd", ("bool", False), "a", "odd", ("len", 1)])
    def gen():
        yield 1 in [Odd(Truth(True))]
    check(lambda: list(gen()), [True], ["odd", ("bool", True)])
    log.clear()
    assert_raises(ValueError, lambda: 1 in [Odd(Truth("bad")), Odd(Truth(True))], message="bool")
    assert_eq(log, ["odd", ("bool", "bad")])
    assert_raises(TypeError, lambda: [Odd(Truth(1))].index(1), message="Truth.__bool__() must return a bool, not int")
main()

check(lambda: 1 in [Odd(Truth(False)), Odd(Truth(True))], True, ["odd", ("bool", False), "odd", ("bool", True)])
