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

# A counter's step: small integers sum in place, and a sum past 64 bits, a
# float, a str or an unbound name take the general path, in a module's
# globals and in a function's locals alike.
big = 2 ** 63 - 2
for _ in range(3):
    big += 1
assert_eq(big, 2 ** 63 + 1)
small = -2 ** 63 + 1
small -= 1
small -= 1
assert_eq(small, -2 ** 63 - 1)
def steps():
    n, f, s = 0, 0.5, "a"
    for i in range(4):
        n += i
        n -= 1
        f += 1
        s += "b"
    return n, f, s
assert_eq(steps(), (2, 4.5, "abbbb"))
def unbound():
    counter += 1
    counter = 0
try:
    unbound()
    assert_true(False, "no error")
except UnboundLocalError as error:
    assert_eq(str(error), "cannot access local variable 'counter' where it is not associated with a value")
class Counted(int):
    def __add__(self, other):
        return "added"
c = Counted(1)
c += 1
assert_eq(c, "added")

# Inside a function, methods that loop take the same fallbacks: __iadd__,
# then on NotImplemented __add__ and the reflected __radd__; a subscript
# or attribute target evaluates its object and key once, reads through
# __getitem__ or __getattr__ and stores through __setitem__.
log = []
def spin():
    for _ in range(2): pass
class Into:
    def __iadd__(self, o): spin(); log.append("iadd"); return "i"
class Declining:
    def __iadd__(self, o): spin(); log.append("iadd"); return NotImplemented
    def __add__(self, o): spin(); log.append("add"); return "a"
class Unadding:
    def __add__(self, o): spin(); log.append("add"); return NotImplemented
class Radding:
    def __radd__(self, o): spin(); log.append("radd"); return "r"
class Plain: pass
class Box:
    def __init__(self): self.items = {"k": 1}
    def __getitem__(self, k): spin(); log.append("get " + k); return self.items[k]
    def __setitem__(self, k, v): spin(); log.append("set " + k); self.items[k] = v
    def __getattr__(self, name): spin(); log.append("attr " + name); return 10
def key(k):
    log.append("key")
    return k
def box(b):
    log.append("box")
    return b
def fallbacks():
    out = []
    for x, y in ((Into(), 1), (Declining(), 1), (Unadding(), Radding()), (Unadding(), 1), (Plain(), 2), (Declining(), None)):
        try:
            x += y
            out.append(x)
        except TypeError as e:
            out.append(str(e))
    b = Box()
    box(b)[key("k")] += 5
    box(b).total += 1
    out.append((b.items, b.total))
    return out
assert_eq(fallbacks(), ["i", "a", "r",
    "unsupported operand type(s) for +=: 'Unadding' and 'int'",
    "unsupported operand type(s) for +=: 'Plain' and 'int'", "a", ({"k": 6}, 11)])
assert_eq(log, ["iadd", "iadd", "add", "add", "radd", "add", "iadd", "add",
    "box", "key", "get k", "set k", "box", "attr total"])
