# spec: reference/datamodel.html#implementing-descriptors
# description: __get__/__set__/__delete__/__set_name__, binding, and the property/classmethod/staticmethod descriptors.
from harness import *

class Named:
    def __set_name__(self, owner, name):
        self.owner, self.name = owner, name
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__.get(self.name, "unset " + self.name)
    def __set__(self, obj, value):
        obj.__dict__[self.name] = value * 2
    def __delete__(self, obj):
        obj.__dict__.pop(self.name)
class T:
    a = Named()
    b = Named()
assert_eq((T.a.owner, T.a.name, T.b.name), (T, "a", "b"))
t = T()
assert_eq(t.a, "unset a")
t.a = 5
assert_eq(t.a, 10)
del t.a
assert_eq(t.a, "unset a")
assert_is(T.__dict__["a"], T.a)

# __set_name__ is called by type.__new__ only, not for later assignment.
n = Named()
T.c = n
assert_false(hasattr(n, "name"))
# __set_name__ errors propagate.
class BadName:
    def __set_name__(self, owner, name):
        raise ZeroDivisionError
def make():
    class X:
        x = BadName()
assert_raises(ZeroDivisionError, make)

# Functions are non-data descriptors producing bound methods.
class M:
    def f(self, x):
        return (self, x)
m = M()
bound = m.f
assert_is(bound.__self__, m)
assert_is(bound.__func__, M.__dict__["f"])
assert_eq(bound(1), (m, 1))
assert_eq(M.f(m, 2), (m, 2))
assert_eq(M.__dict__["f"].__get__(m, M)(3), (m, 3))
assert_true(m.f == m.f)
assert_false(m.f is m.f)
assert_eq(type(bound).__name__, "method")

class K:
    @classmethod
    def c(cls, x):
        return (cls, x)
    @staticmethod
    def s(x):
        return x
class K2(K): pass
assert_eq(K2.c(1), (K2, 1))
assert_eq(K2().c(1), (K2, 1))
assert_eq(K().s(4), 4)
assert_eq(K.s(4), 4)
assert_true(callable(K.__dict__["s"]))  # staticmethod objects are callable (3.10+)
assert_eq(K.__dict__["s"](5), 5)

# property: getter/setter/deleter and copies.
class Temp:
    def __init__(self):
        self._c = 0
    @property
    def c(self):
        "Celsius"
        return self._c
    @c.setter
    def c(self, v):
        self._c = v
    @c.deleter
    def c(self):
        self._c = None
x = Temp()
x.c = 30
assert_eq(x.c, 30)
del x.c
assert_is(x.c, None)
assert_eq(Temp.c.__doc__, "Celsius")
ro = property(lambda self: 1)
class RO:
    v = ro
assert_raises(AttributeError, setattr, RO(), "v", 2)
assert_raises(AttributeError, delattr, RO(), "v")
assert_is(RO.v, ro)

# __get__ is looked up on the type of the descriptor.
class Inst:
    pass
i = Inst()
i.__get__ = lambda *a: "never"
class Holder:
    attr = i
assert_is(Holder.attr, i)

# A data descriptor without __get__ yields to the instance dictionary on
# reads, and is returned itself when the dictionary lacks the name.
class SetOnly:
    def __set__(self, instance, value):
        instance.__dict__["seen"] = value
class Holder:
    x = SetOnly()
holder = Holder()
assert_true(holder.x is Holder.__dict__["x"])
holder.__dict__["x"] = "inst"
assert_eq(holder.x, "inst")
holder.x = 5
assert_eq((holder.x, holder.seen), ("inst", 5))
