# spec: PLS-315 13.10, 7.2.5, 7.2.4
# description: in and not in of a generator, or of an instance iterated by
# its __iter__, test the truth of each item's Python __eq__ result, or of
# x's reflected one after the item's declined, by its Python __bool__, or
# __len__ without one, which may loop; a true result ends the search past
# that item, a false one goes on, a __bool__ that returns no bool raises
# TypeError, and errors propagate. Inside functions and generators as at
# module level.
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
    def __eq__(self, other): spin(); log.append("declines"); return NotImplemented
class Iterated:
    def __init__(self, *items): self.items = items
    def __iter__(self): return iter(self.items)

def items(*xs):
    yield from xs

def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def main():
    check(lambda: 1 in items(Odd(Truth(False)), Odd(Sized(0)), Odd(Truth(True)), 4), True,
          ["odd", ("bool", False), "odd", ("len", 0), "odd", ("bool", True)])
    check(lambda: 1 not in items(Odd(Sized(3))), False, ["odd", ("len", 3)])
    check(lambda: Odd(Truth(True)) in items(Declining()), True, ["declines", "odd", ("bool", True)])
    check(lambda: 1 in Iterated(Odd(Truth(False))), False, ["odd", ("bool", False)])
    rest = items(Odd(Truth(True)), 7)
    check(lambda: (1 in rest, list(rest)), (True, [7]), ["odd", ("bool", True)])
    def gen():
        yield 1 in items(Odd(Truth(True)))
    check(lambda: list(gen()), [True], ["odd", ("bool", True)])
    log.clear()
    assert_raises(ValueError, lambda: 1 in items(Odd(Truth("bad")), Odd(Truth(True))), message="bool")
    assert_eq(log, ["odd", ("bool", "bad")])
    assert_raises(TypeError, lambda: 1 in items(Odd(Truth(2))), message="Truth.__bool__() must return a bool, not int")
main()

check(lambda: 1 in items(Odd(Truth(False)), Odd(Truth(True))), True, ["odd", ("bool", False), "odd", ("bool", True)])
