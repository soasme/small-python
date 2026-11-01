# spec: PLS-315 14.3, 7.6.3
# description: Augmented assignment with __iadd__ and friends and their fallbacks.
from harness import *
class InPlace:
    def __init__(self, val):
        self.val = val

    def __ipow__(self, other):
        self.val **= other
        return self

    def __imul__(self, other):
        self.val *= other
        return self

    def __imatmul__(self, other):
        # I guess you could think of an int as a 1x1 matrix
        self.val *= other
        return self

    def __itruediv__(self, other):
        self.val /= other
        return self

    def __ifloordiv__(self, other):
        self.val //= other
        return self

    def __imod__(self, other):
        self.val %= other
        return self

    def __iadd__(self, other):
        self.val += other
        return self

    def __isub__(self, other):
        self.val -= other
        return self

    def __ilshift__(self, other):
        self.val <<= other
        return self

    def __irshift__(self, other):
        self.val >>= other
        return self

    def __iand__(self, other):
        self.val &= other
        return self

    def __ixor__(self, other):
        self.val ^= other
        return self

    def __ior__(self, other):
        self.val |= other
        return self


i = InPlace(2)
i **= 3
assert i.val == 8

i = InPlace(2)
i *= 2
assert i.val == 4

i = InPlace(2)
i @= 2
assert i.val == 4

i = InPlace(1)
i /= 2
assert i.val == 0.5

i = InPlace(1)
i //= 2
assert i.val == 0

i = InPlace(10)
i %= 3
assert i.val == 1

i = InPlace(1)
i += 1
assert i.val == 2

i = InPlace(2)
i -= 1
assert i.val == 1

i = InPlace(2)
i <<= 3
assert i.val == 16

i = InPlace(16)
i >>= 3
assert i.val == 2

i = InPlace(0b010101)
i &= 0b111000
assert i.val == 0b010000

i = InPlace(0b010101)
i ^= 0b111000
assert i.val == 0b101101

i = InPlace(0b010101)
i |= 0b111000
assert i.val == 0b111101

# Numbers without a shared in-place operator name the augmented operator.
def shift(x, y):
    x <<= y
def matmul(x, y):
    x @= y
assert_raises(TypeError, shift, 7.5, 2, message="unsupported operand type(s) for <<=: 'float' and 'int'")
assert_raises(TypeError, matmul, 7, 2, message="unsupported operand type(s) for @=: 'int' and 'int'")
x = 7
x //= 2
x **= 2
x <<= 1
assert x == 18
x = 7.5
x /= 2
x %= 2
assert x == 1.75

# list and bytearray concatenation and repetition rank after the operand's
# reflected method; set in-place operators accept any set operand first.
class Reflected:
    def __radd__(self, o): return "radd"
    def __rmul__(self, o): return "rmul"
for seq in ([1], bytearray(b"a")):
    x = seq
    x += Reflected()
    assert x == "radd"
    x = seq
    x *= Reflected()
    assert x == "rmul"
class SubList(list): pass
x = SubList([1])
x *= Reflected()
assert x == "rmul"
x = SubList([1])
x += [2]
assert x == [1, 2]
class Declines:
    def __radd__(self, o): return NotImplemented
x = [1]
assert_raises(TypeError, lambda: x.__iadd__(Declines()), message="'Declines' object is not iterable")
class OrSet(set):
    def __ror__(self, o): return "ror"
s = {1}
alias = s
s |= OrSet({2})
assert s is alias and s == {1, 2}

# Operations a builtin base does not perform in place reflect with the
# subclass instance itself.
class Witness:
    def __rsub__(self, o): return type(o)
    def __ror__(self, o): return type(o)
class SubSet(set): pass
class SubDict(dict): pass
x = SubList([1])
x -= Witness()
assert x is SubList
x = SubSet({1})
x |= Witness()
assert x is SubSet
x = SubDict(a=1)
x -= Witness()
assert x is SubDict
x = SubDict(a=1)
assert_raises(TypeError, lambda: x.__ior__(Witness()), message="'Witness' object is not iterable")
