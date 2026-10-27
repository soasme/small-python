# spec: PLS-315 13.5, 7.6.2
# description: ** binds tighter than a unary operator on its left, looser than one on its right, and groups right to left.
from harness import *

assert_eq(-2 ** 2, -4)
assert_eq((-2) ** 2, 4)
assert_eq(2 ** -1, 0.5)
assert_eq(2 ** 3 ** 2, 512)
assert_eq((2 ** 3) ** 2, 64)
assert_eq(~2 ** 2, -5)
assert_eq(2 ** ~0, 0.5)
assert_same(2 ** 10, 1024)
assert_same(2.0 ** 2, 4.0)
assert_same(4 ** 0.5, 2.0)
assert_same(10 ** -2, 0.01)
assert_same(0 ** 0, 1)
assert_eq((-8) ** (1 / 3) == complex, False)
assert_type((-8) ** 0.5, complex)
e = assert_raises(ZeroDivisionError, lambda: 0 ** -1)
assert_eq(str(e), "zero to a negative power")
assert_eq(pow(2, 10, 1000), 24)

# BinaryOp dispatch: __pow__, then the reflected __rpow__.
class P:
    def __pow__(self, other):
        return ("pow", other)
    def __rpow__(self, other):
        return ("rpow", other)
assert_eq(P() ** 3, ("pow", 3))
assert_eq(3 ** P(), ("rpow", 3))
e = assert_raises(TypeError, lambda: "a" ** 2)
assert_eq(str(e), "unsupported operand type(s) for ** or pow(): 'str' and 'int'")

# An await_primary may be the base: await x ** 2 is (await x) ** 2.
assert_compiles("async def f():\n    return await x ** 2\n")
