# spec: PLS-315 20.3.1, 8.6
# description: A list, set or dictionary comprehension calls super() in its function's frame, and an assignment expression nested in its displays binds in that scope.
from harness import *


class Base:
    def method(self):
        return 1


class Derived(Base):
    def lists(self):
        return [super().method() for _ in range(2)]

    def sets(self):
        return {super().method() for _ in range(2)}

    def dicts(self):
        return {i: super().method() for i in range(2)}


value = Derived()
assert_eq(value.lists(), [1, 1])
assert_eq(value.sets(), {1})
assert_eq(value.dicts(), {0: 1, 1: 1})


def identity(a):
    return a


def nested():
    rows = [[y := identity(x), x // y] for x in range(1, 4)]
    return rows, y


assert_eq(nested(), ([[1, 1], [2, 1], [3, 1]], 3))
rows = [(z := identity(x), [w := z * 2]) for x in range(3)]
assert_eq((rows[-1], z, w), ((2, [4]), 2, 4))
