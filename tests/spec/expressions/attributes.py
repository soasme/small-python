# spec: PLS-315 13.3.1
# description: Attribute assignment, lookup, and deletion on instances and classes.
from harness import *


class A:
    pass

class B:
    x = 50

a = A()
a.b = 10
assert hasattr(a, 'b')
assert a.b == 10

assert B.x == 50

# test delete class attribute with del keyword
del B.x
with assert_raises(AttributeError):
    _ = B.x

# test override attribute
setattr(a, 'b', 12)
assert a.b == 12
assert getattr(a, 'b') == 12

# test non-existent attribute
with assert_raises(AttributeError):
    _ = a.c

with assert_raises(AttributeError):
    getattr(a, 'c')

assert getattr(a, 'c', 21) == 21

# test set attribute
setattr(a, 'c', 20)
assert hasattr(a, 'c')
assert a.c == 20

# test delete attribute
delattr(a, 'c')
assert not hasattr(a, 'c')
with assert_raises(AttributeError):
    _ = a.c


# test setting attribute on builtin
with assert_raises(AttributeError):
    object().a = 1

with assert_raises(AttributeError):
    del object().a

with assert_raises(AttributeError):
    setattr(object(), 'a', 2)

with assert_raises(AttributeError):
    delattr(object(), 'a')

attrs = {}


class CustomLookup:
    def __getattr__(self, item):
        return "value_{}".format(item)

    def __setattr__(self, key, value):
        attrs[key] = value


custom = CustomLookup()

assert custom.attr == "value_attr"

custom.a = 2
custom.b = 5
assert attrs['a'] == 2
assert attrs['b'] == 5


class GetRaise:
    def __init__(self, ex):
        self.ex = ex

    def __getattr__(self, item):
        raise self.ex


assert not hasattr(GetRaise(AttributeError()), 'a')
with assert_raises(AttributeError):
    getattr(GetRaise(AttributeError()), 'a')
assert getattr(GetRaise(AttributeError()), 'a', 11) == 11

with assert_raises(KeyError):
    hasattr(GetRaise(KeyError()), 'a')
with assert_raises(KeyError):
    getattr(GetRaise(KeyError()), 'a')
with assert_raises(KeyError):
    getattr(GetRaise(KeyError()), 'a', 11)


# Attributes as operands: each is looked up as an ordinary attribute
# reference, and an operator method may delete the attributes it was given.
class Deleting:
    def __init__(self, box):
        self.box = box

    def __add__(self, other):
        del self.box.left, other.box.right
        return [self.box] * 2


box = A()
for _ in range(3):
    box.left = Deleting(box)
    box.right = Deleting(box)
    assert box.left + box.right == [box, box]
    assert not hasattr(box, 'left') and not hasattr(box, 'right')

point = A()
point.x = 3
seen = []
for step in range(4):
    if step == 2:
        A.x = property(lambda self: 10)
    seen.append((point.x + point.x, point.x < 5))
assert seen == [(6, True), (6, True), (20, False), (20, False)]
del A.x
del point.x
with assert_raises(AttributeError):
    point.x + 1
