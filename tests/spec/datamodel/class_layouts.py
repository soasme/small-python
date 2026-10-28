# spec: PLS-315 10.1.2, 10.1.3, 10.2.1, 10.2.2, 10.4.2, 20.3.2
# description: Instance layouts decide __class__ and __bases__ assignment; builtin __new__ entries keep the inherited allocator; super subclasses bind and reinitialize.
from harness import *


def layout_error(action):
    error = assert_raises(TypeError, action)
    assert_true("layout differs" in str(error), str(error))


# 10.1.2: one generic __dict__ and __weakref__ getset serves every class.
class Plain:
    pass


class Slotted:
    __slots__ = ["x"]


class Sub(Slotted):
    pass


assert_is(Sub.__dict__["__dict__"], Plain.__dict__["__dict__"])
assert_is(Plain.__dict__["__weakref__"].__objclass__, object)
assert_raises(AttributeError, Plain.__dict__["__weakref__"].__get__, Slotted(), Slotted)
assert_eq(Plain.__dict__["__weakref__"].__get__(Plain(), Plain), None)


class Classcell:
    __slots__ = ["__classcell__"]

    def method(self):
        return __class__


assert_type(Classcell.__dict__["__classcell__"], type(Slotted.__dict__["x"]))


# Variable-size layouts take weak references only through __slots__.
class Weak(int):
    __slots__ = ["__weakref__"]


class Strong(int):
    pass


assert_true(hasattr(Weak(1), "__weakref__"))
assert_false(hasattr(Strong(1), "__weakref__"))
weak = Weak(5)
assert_is(host.weak_reference(weak)(), weak)
assert_raises(TypeError, host.weak_reference, Strong(5))

# 10.1.3: weak reference support is part of the layout.
class J:
    __slots__ = ["b"]


class N(J):
    __slots__ = ["__weakref__"]


def assign(obj, cls):
    obj.__class__ = cls


layout_error(lambda: assign(J(), N))
layout_error(lambda: assign(N(), J))


# 10.4.2: the layout instances would get, and restoration on failure.
class A:
    __slots__ = ()


class WithDict:
    pass


class B:
    __slots__ = ()


layout_error(lambda: setattr(B, "__bases__", (int,)))
layout_error(lambda: setattr(B, "__bases__", (WithDict,)))
assert_eq(B.__bases__, (object,))
B.__bases__ = (A,)
assert_eq(B.__mro__, (B, A, object))


class Own:
    pass


Own.__bases__ = (WithDict,)
Own.__bases__ = (A,)
error = assert_raises(TypeError, setattr, B, "__bases__", (bool,))
assert_eq(str(error), "type 'bool' is not an acceptable base type")


class Once(type):
    def mro(cls):
        if getattr(cls, "fail", False):
            raise RuntimeError
        return type.mro(cls)


class C:
    pass


class C2:
    pass


class D(C):
    pass


class E(D):
    pass


class F(D, metaclass=Once):
    pass


F.fail = True
before = (D.__mro__, E.__mro__)
assert_raises(RuntimeError, setattr, D, "__bases__", (C2,))
assert_eq((D.__bases__, D.__mro__, E.__mro__), ((C,),) + before)


# A custom MRO that leaves the class out fails at __init_subclass__.
class Outside(type):
    def mro(cls):
        return (C,)


error = assert_raises(TypeError, Outside, "X", (), {})
assert_eq(str(error), "super(type, obj): obj (type X) is not an instance or subtype of type (X).")


# 10.2.1: a builtin class's __new__ in a class body keeps the inherited one.
class ListNew:
    __new__ = list.__new__


assert_type(ListNew(), ListNew)


class Base:
    def __new__(cls, *args):
        raise AssertionError


class Restored(Base):
    __new__ = object.__new__

    def __init__(self, value):
        self.value = value


error = assert_raises(TypeError, Restored, 3)
assert_eq(str(error), "object.__new__() takes exactly one argument (the type to instantiate)")
assert_eq(str(assert_raises(TypeError, object.__new__)), "object.__new__(): not enough arguments")


# 20.3.2: super subclasses.
class Root:
    def name(self):
        return "Root"


class MySuper(super):
    def __init__(self, *args):
        super(MySuper, self).__init__(*args)


class Leaf(Root):
    def name(self):
        return "Leaf" + self.__up.name()


Leaf._Leaf__up = MySuper(Leaf)
assert_eq(Leaf().name(), "LeafRoot")
assert_type(Leaf()._Leaf__up, MySuper)
