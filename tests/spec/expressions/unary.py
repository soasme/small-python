# spec: PLS-315 13.6
# description: Unary -, +, ~ on numbers, instances, and classes with metaclass slots.
from harness import *


class A:
    def __neg__(self):
        return "neg"

    def __pos__(self):
        return "pos"

    def __abs__(self):
        return "abs"

    def __invert__(self):
        return "invert"


a = A()
assert -a == "neg"
assert +a == "pos"
assert abs(a) == "abs"
assert ~a == "invert"


class I(int):
    def __neg__(self):
        return "I.neg"


assert -I(3) == "I.neg"
assert +I(3) == 3
assert abs(I(-3)) == 3
assert ~I(3) == -4


# Slots follow methods assigned or deleted after class creation.
class Late:
    pass


with assert_raises(TypeError):
    -Late()
Late.__neg__ = lambda self: "late"
assert -Late() == "late"
del Late.__neg__
with assert_raises(TypeError):
    -Late()

del I.__neg__
assert -I(3) == -3

# Only the type is consulted, not the instance.
i = Late()
i.__neg__ = lambda: "instance"
with assert_raises(TypeError):
    -i


class Meta(type):
    def __neg__(cls):
        return cls.__name__


class WithMeta(metaclass=Meta):
    pass


assert -WithMeta == "WithMeta"

with assert_raises(TypeError) as cm:
    -"a"
assert str(cm.exception) == "bad operand type for unary -: 'str'"
with assert_raises(TypeError) as cm:
    abs([])
assert str(cm.exception) == "bad operand type for abs(): 'list'"

# A class's unary operator comes from its metaclass.
class Plain(type): pass
class WithPlain(metaclass=Plain): pass
assert_raises(TypeError, lambda: -WithPlain, message="bad operand type for unary -: 'Plain'")
class Negating(type):
    def __neg__(cls): return "neg"
class WithNegating(metaclass=Negating): pass
assert_eq(-WithNegating, "neg")

# Inside a function, a special method that loops runs the same way; a
# __pos__ returning NotImplemented returns it, `not` asks __bool__.
class Looping:
    def __neg__(self):
        for _ in range(2): pass
        return "neg"
    def __pos__(self): return NotImplemented
    def __invert__(self, extra): return 1
    def __bool__(self): return False
def unary_in_function():
    u = Looping()
    out = [-u, +u is NotImplemented, not u, -I(3), ~I(3)]
    for x, op in ((u, "~"), (Late(), "-")):
        try:
            out.append(~x if op == "~" else -x)
        except TypeError as e:
            out.append(str(e))
    return out
assert_eq(unary_in_function(), ["neg", True, True, -3, -4,
          "Looping.__invert__() missing 1 required positional argument: 'extra'",
          "bad operand type for unary -: 'Late'"])
