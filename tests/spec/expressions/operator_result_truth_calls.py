# spec: PLS-315 13.10, 7.2.4
# description: != of an object whose class defines __eq__ but not __ne__
# inverts the truth of what that Python __eq__ returned, and in and not in
# of an instance take the truth of what its Python __contains__ returned;
# a result's truth is tested by its Python __bool__, or __len__ without
# one, which may loop. A __bool__ that returns no bool, or that cannot be
# called, raises TypeError. Inside functions, generators, comprehensions,
# tests and boolean operations, as at module level.
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
    def __init__(self, n): self.n = n
    def __len__(self): spin(); log.append(("len", self.n)); return self.n
class Odd:
    def __init__(self, result): self.result = result
    def __eq__(self, other): spin(); return self.result
class Box:
    def __init__(self, result): self.result = result
    def __contains__(self, x): spin(); return self.result
class Uncallable:
    def __bool__(self, extra): return True

def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def main():
    check(lambda: (Odd(Truth(True)) != 1, Odd(Truth(False)) != 1), (False, True), [("bool", True), ("bool", False)])
    check(lambda: (Odd(Sized(0)) != 1, Odd(Sized(2)) != 1), (True, False), [("len", 0), ("len", 2)])
    check(lambda: (1 in Box(Truth(True)), 1 not in Box(Truth(True)), 1 in Box(Sized(0)), 1 in Box(3)), (True, False, False, True),
          [("bool", True), ("bool", True), ("len", 0)])
    def gen():
        yield Odd(Truth(True)) != 1
        yield 1 in Box(Truth(False))
    check(lambda: list(gen()), [False, False], [("bool", True), ("bool", False)])
    check(lambda: [1 in Box(Truth(True)) for _ in range(2)], [True, True], [("bool", True), ("bool", True)])
    check(lambda: "ne" if Odd(Truth(False)) != 1 else "eq", "ne", [("bool", False)])
    check(lambda: 1 in Box(Truth(True)) and 5, 5, [("bool", True)])
    assert_raises(TypeError, lambda: Odd(Truth(2)) != 1, message="Truth.__bool__() must return a bool, not int")
    assert_raises(TypeError, lambda: 1 in Box(Truth(2)), message="Truth.__bool__() must return a bool, not int")
    assert_raises(TypeError, lambda: 1 in Box(Uncallable()), message="Uncallable.__bool__() missing 1 required positional argument: 'extra'")
    assert_raises(TypeError, lambda: Odd(Uncallable()) != 1, message="Uncallable.__bool__() missing 1 required positional argument: 'extra'")
main()

check(lambda: (Odd(Truth(True)) != 1, 1 in Box(Truth(True))), (False, True), [("bool", True), ("bool", True)])
