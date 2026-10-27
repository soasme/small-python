# spec: PLS-315 8.5, 16.4.3, 20.3.1
# description: A method that uses super or __class__ gets the implicit __class__ cell of its class.
from harness import *

class A:
    def who(self):
        return "A"
class B(A):
    def who(self):
        return "B" + super().who()
    def cls(self):
        return __class__
    def nested(self):
        def inner():
            return __class__
        return inner()
    def via_lambda(self):
        return (lambda: super())().who()
    def plain(self):
        return 1
assert_eq(B().who(), "BA")
assert_is(B().cls(), B)
assert_is(B().nested(), B)
# A nested function sees the cell, but super() needs its own first argument.
e = assert_raises(RuntimeError, B().via_lambda)
assert_eq(str(e), "super(): no arguments")
assert_true("__class__" in B.cls.__code__.co_freevars)
assert_true("__class__" in B.who.__code__.co_freevars)
assert_false("__class__" in B.plain.__code__.co_freevars)
assert_true("__class__" in B.nested.__code__.co_cellvars or "__class__" in B.nested.__code__.co_freevars)

# The cell is set to the new class, also for a subclass that inherits the method.
class Sub(B):
    pass
assert_is(Sub().cls(), B)

# The class body sees __classcell__ and the metaclass must pass it on.
seen = []
class Meta(type):
    def __new__(meta, name, bases, ns):
        seen.append("__classcell__" in ns)
        return super().__new__(meta, name, bases, ns)
class WithCell(metaclass=Meta):
    def f(self):
        return __class__
class WithoutCell(metaclass=Meta):
    def f(self):
        return 1
assert_eq(seen, [True, False])
assert_is(WithCell().f(), WithCell)

# A __class__ name in the class body itself is not the cell.
class Body:
    __class__ = "attr"
assert_eq(Body.__dict__["__class__"], "attr")

# super() without a cell fails.
def loose(self):
    return super()
e = assert_raises(RuntimeError, loose, object())
assert_eq(str(e), "super(): __class__ cell not found")
