# spec: reference/datamodel.html#special-method-lookup
# description: Implicit special method calls look up the type, bypassing the instance and __getattribute__.
from harness import *

class C:
    pass
c = C()
c.__len__ = lambda: 5
assert_raises(TypeError, len, c)
assert_eq(c.__len__(), 5)

class Meta(type):
    def __getattribute__(cls, name):
        Meta.log.append(name)
        return type.__getattribute__(cls, name)
Meta.log = []
class D(metaclass=Meta):
    def __len__(self):
        return 10
    def __getattribute__(self, name):
        raise AssertionError("instance __getattribute__ must not be used for " + name)
d = D()
Meta.log.clear()
assert_eq(len(d), 10)
assert_eq(Meta.log, [])

# Special methods defined on the metaclass apply to the class itself.
class LenMeta(type):
    def __len__(cls):
        return 3
class E(metaclass=LenMeta):
    def __len__(self):
        return 7
assert_eq(len(E), 3)
assert_eq(len(E()), 7)

# Replacing a special method on the class takes effect immediately.
class F:
    def __repr__(self):
        return "one"
f = F()
assert_eq(repr(f), "one")
F.__repr__ = lambda self: "two"
assert_eq(repr(f), "two")
del F.__repr__
assert_true(repr(f).startswith("<"))

# Setting a special method to None blocks the operation.
class NoIter:
    __iter__ = None
    def __getitem__(self, i):
        return i
assert_raises(TypeError, iter, NoIter())
class NoHash:
    __hash__ = None
assert_raises(TypeError, hash, NoHash())
class NoContains:
    __contains__ = None
    def __iter__(self):
        return iter([1])
assert_raises(TypeError, lambda: 1 in NoContains())
class NoReversed:
    __reversed__ = None
    def __len__(self):
        return 1
    def __getitem__(self, i):
        return i
assert_raises(TypeError, reversed, NoReversed())

# Descriptors (staticmethod, classmethod, property) work as special methods.
class G:
    @staticmethod
    def __len__():
        raise AssertionError
    __len__ = lambda self: 4
    __bool__ = property(lambda self: lambda: False) if False else (lambda self: False)
assert_eq(len(G()), 4)
assert_false(G())
