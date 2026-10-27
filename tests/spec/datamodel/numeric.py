# spec: PLS-315 7.6
# description: Binary, reflected and in-place operator dispatch, NotImplemented, unary and conversion methods.
from harness import *

class N:
    def __init__(self, v): self.v = v
    def __add__(self, o): return ("add", o)
    def __radd__(self, o): return ("radd", o)
    def __iadd__(self, o): return ("iadd", o)
    def __sub__(self, o): return NotImplemented
    def __rsub__(self, o): return ("rsub", o)
    def __neg__(self): return "neg"
    def __pos__(self): return "pos"
    def __abs__(self): return "abs"
    def __invert__(self): return "inv"
    def __index__(self): return self.v
    def __matmul__(self, o): return "matmul"
    def __rpow__(self, o): return ("rpow", o)
    def __divmod__(self, o): return "divmod"
n = N(3)
assert_eq(n + 1, ("add", 1))
assert_eq(1 + n, ("radd", 1))
# The reflected method is not tried for operands of the same type.
assert_raises(TypeError, lambda: n - n)
assert_eq(1 - n, ("rsub", 1))
x = n
x += 1
assert_eq(x, ("iadd", 1))
assert_eq((-n, +n, abs(n), ~n), ("neg", "pos", "abs", "inv"))
assert_eq([0, 1, 2, 3, 4][n], 3)
assert_eq(bin(n), "0b11")
assert_eq(range(10)[N(2):N(4)], range(2, 4))
assert_eq(n @ n, "matmul")
assert_eq(2 ** n, ("rpow", 2))
assert_eq(divmod(n, 1), "divmod")
assert_raises(TypeError, lambda: n * 2)
assert_raises(TypeError, lambda: n / 2)
assert_raises(TypeError, lambda: n < 2)

# Subclass reflected methods take priority when they override.
class A:
    def __add__(self, o): return "A.add"
    def __radd__(self, o): return "A.radd"
class B(A):
    def __radd__(self, o): return "B.radd"
assert_eq(A() + B(), "B.radd")
class C(A): pass
assert_eq(A() + C(), "A.add")

# In-place falls back to the binary operator.
class Plain:
    def __add__(self, o): return "plain"
p = Plain()
p += 1
assert_eq(p, "plain")
l = [1]
alias = l
l += [2]
assert_is(l, alias)
t = (1,)
alias = t
t += (2,)
assert_false(t is alias)

class Conv:
    def __int__(self): return 7
    def __float__(self): return 2.5
    def __complex__(self): return 1j
    def __round__(self, n=None): return ("round", n)
    def __trunc__(self): return "trunc"
    def __floor__(self): return "floor"
    def __ceil__(self): return "ceil"
c = Conv()
assert_eq((int(c), float(c), complex(c)), (7, 2.5, 1j))
assert_eq(round(c), ("round", None))
assert_eq(round(c, 2), ("round", 2))
class BadInt:
    def __int__(self): return "x"
assert_raises(TypeError, int, BadInt())
class BadIndex:
    def __index__(self): return 1.0
assert_raises(TypeError, lambda: [1][BadIndex()])
key = "0"
assert_raises(TypeError, lambda: [1][key])
# Builtin numeric tower behaviour.
assert_same(True + True, 2)
assert_same(7 // 2, 3)
assert_same(-7 // 2, -4)
assert_same(-7 % 3, 2)
assert_same(7 % -3, -2)
assert_same(7.0 // 2, 3.0)
assert_same(2 ** -1, 0.5)
assert_same((-8) ** (1/3) == (-8) ** (1/3), True)
assert_eq(type((-8) ** 0.5), complex)
assert_raises(ZeroDivisionError, lambda: 1 // 0)
assert_raises(ZeroDivisionError, lambda: 1 % 0.0)
assert_raises(ZeroDivisionError, lambda: 0 ** -1)
assert_same(1 << 3, 8)
assert_raises(ValueError, lambda: 1 << -1)
assert_same(-1 >> 10, -1)
assert_same(5 & 3 | 8 ^ 1, 9)
assert_same(divmod(-7, 2), (-4, 1))
