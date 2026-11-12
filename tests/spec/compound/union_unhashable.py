# spec: PLS-315 29.5.1, 29.5.2
# description: MakeUnion compares hashable members by hash and unhashable ones by equality, and a union with unhashable members is unhashable even once they hash.
from harness import *

class BadEq(type):
    def __eq__(self, other):
        return 1 / 0

A = BadEq('A', (), {})
B = BadEq('B', (), {})
# A hashable member is found by hash, so A's __eq__ is not called for int.
u = int | A
assert_eq(u.__args__, (int, A))
assert_eq((A | int | int).__args__, (A, int))
# An unhashable member is compared with the earlier unhashable ones.
assert_raises(ZeroDivisionError, lambda: A | B)
assert_raises(ZeroDivisionError, lambda: u == (int | B))
assert_true((int | A) == (A | int))

state = []
class Flaky(type):
    def __hash__(self):
        if state:
            return 1
        raise TypeError("not hashable")

C = Flaky('C', (), {})
D = Flaky('D', (), {})
v = C | D
assert_raises(TypeError, hash, v, message="not hashable")
state.append(1)
assert_raises(TypeError, hash, v, message="union contains 2 unhashable elements")
assert_eq(hash(int | str), hash(str | int))
assert_true((C | int) != (int | str))
