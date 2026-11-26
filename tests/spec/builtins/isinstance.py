# spec: PLS-315 19.3.21, 7.1.3
# description: isinstance() with tuples, unions, and __instancecheck__; an
# AttributeError from an instance's __class__ means False, another error
# propagates.
from harness import *
class Regular:
    pass


assert isinstance(Regular(), Regular)


class MCNotInstanceOf(type):
    def __instancecheck__(self, instance):
        return False


class NotInstanceOf(metaclass=MCNotInstanceOf):
    pass


class InheritedNotInstanceOf(NotInstanceOf):
    pass


assert not isinstance(Regular(), NotInstanceOf)
assert not isinstance(1, NotInstanceOf)

# weird cpython behaviour if exact match then isinstance return true
assert isinstance(NotInstanceOf(), NotInstanceOf)
assert not NotInstanceOf.__instancecheck__(NotInstanceOf())
assert not isinstance(InheritedNotInstanceOf(), NotInstanceOf)


class MCAlwaysInstanceOf(type):
    def __instancecheck__(self, instance):
        return True


class AlwaysInstanceOf(metaclass=MCAlwaysInstanceOf):
    pass


assert isinstance(AlwaysInstanceOf(), AlwaysInstanceOf)
assert isinstance(Regular(), AlwaysInstanceOf)
assert isinstance(1, AlwaysInstanceOf)


class GenericInstance:
    def __instancecheck__(self, _):
        return True


assert isinstance(Regular(), GenericInstance())
assert isinstance([], GenericInstance())
assert isinstance(1, GenericInstance())


class MCReturnInt(type):
    def __instancecheck__(self, instance):
        return 3


class ReturnInt(metaclass=MCReturnInt):
    pass


assert isinstance("a", ReturnInt) is True

assert isinstance(
    1,
    (
        (
            int,
            float,
        ),
        str,
    ),
)

# An AttributeError from __class__ means the object is not an instance.
class NoClass:
    @property
    def __class__(self):
        raise AttributeError("no")
assert_eq(isinstance(NoClass(), int), False)

# Another error from __class__ propagates, also from type.__instancecheck__.
class BadClass:
    @property
    def __class__(self):
        raise KeyError("bad")
class MCDefault(type):
    def __instancecheck__(cls, instance): return type.__instancecheck__(cls, instance)
class Default(metaclass=MCDefault): pass
assert_raises(KeyError, lambda: isinstance(BadClass(), int))
assert_raises(KeyError, lambda: isinstance(BadClass(), Default))
assert_eq(isinstance(NoClass(), Default), False)
