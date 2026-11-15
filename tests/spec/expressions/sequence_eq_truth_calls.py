# spec: PLS-315 25.5.3, 26.1.2, 7.2.5, 7.2.4
# description: == and != of two lists, two tuples or two dicts test the
# truth of an item's Python __eq__ result, or of the reflected __eq__'s,
# by its Python __bool__, or __len__ without one, which may loop; a false
# result ends the walk at that pair, a true one goes on, a __bool__ that
# returns no bool raises TypeError, and an error from __bool__ or __len__
# propagates. Inside functions, generators and nested sequences, as at
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
    def __eq__(self, other): spin(); return self.result
class Declining:
    def __eq__(self, other): spin(); return NotImplemented

def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def main():
    check(lambda: [Odd(Truth(True)), Odd(Truth(False))] == [1, 2], False, [("bool", True), ("bool", False)])
    check(lambda: (Odd(Truth(False)), Odd(Truth(True))) != (1, 2), True, [("bool", False)])
    check(lambda: [Odd(Sized(2)), Odd(Sized(0))] == [1, 2], False, [("len", 2), ("len", 0)])
    check(lambda: [Declining()] == [Odd(Truth(True))], True, [("bool", True)])
    check(lambda: [[Odd(Truth(True))], Odd(Sized(1))] == [[1], 2], True, [("bool", True), ("len", 1)])
    check(lambda: {1: Odd(Truth(True)), 2: Odd(Truth(False))} == {1: 1, 2: 2}, False, [("bool", True), ("bool", False)])
    def gen():
        yield [Odd(Truth(True))] == [1]
    check(lambda: list(gen()), [True], [("bool", True)])
    log.clear()
    assert_raises(ValueError, lambda: [Odd(Truth("bad")), Odd(Truth(True))] == [1, 2], message="bool")
    assert_eq(log, [("bool", "bad")])
    assert_raises(TypeError, lambda: [Odd(Truth(1))] == [1], message="Truth.__bool__() must return a bool, not int")
main()

check(lambda: [Odd(Truth(True)), 3] == [1, 3], True, [("bool", True)])
