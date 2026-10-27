# spec: reference/datamodel.html#customizing-instance-and-subclass-checks
# description: __instancecheck__, __subclasscheck__, callables, __len__/__bool__, __hash__ rules.
from harness import *

class Meta(type):
    def __instancecheck__(cls, instance): return instance == 42
    def __subclasscheck__(cls, sub): return sub is int
class Answer(metaclass=Meta): pass
assert_true(isinstance(42, Answer))
assert_false(isinstance(41, Answer))
assert_true(issubclass(int, Answer))
assert_false(issubclass(str, Answer))
# Exact type match short-circuits __instancecheck__.
assert_true(isinstance(Answer(), Answer))
assert_true(isinstance(1, (str, int)))
assert_raises(TypeError, isinstance, 1, 1)

class Callable:
    def __call__(self, *a, **k): return a, k
assert_eq(Callable()(1, x=2), ((1,), {"x": 2}))
assert_true(callable(Callable()))
assert_false(callable(object()))

class Lengthy:
    def __len__(self): return 0
assert_false(bool(Lengthy()))
class Truthy:
    def __bool__(self): return False
    def __len__(self): return 1
assert_false(bool(Truthy()))
class BadBool:
    def __bool__(self): return 1
assert_raises(TypeError, bool, BadBool())
class BadLen:
    def __len__(self): return -1
assert_raises(ValueError, bool, BadLen())
class HugeLen:
    def __len__(self): return 2**100
assert_raises(OverflowError, len, HugeLen())

# Defining __eq__ without __hash__ makes instances unhashable.
class Eq:
    def __eq__(self, other): return True
assert_is(Eq.__hash__, None)
assert_raises(TypeError, hash, Eq())
class EqHash(Eq):
    __hash__ = object.__hash__
hash(EqHash())
class BadHash:
    def __hash__(self): return "x"
assert_raises(TypeError, hash, BadHash())
class BigHash:
    def __hash__(self): return 2**100
assert_eq(hash(BigHash()), hash(2**100))
# __ne__ defaults to the inverse of __eq__.
class OnlyEq:
    def __eq__(self, other): return isinstance(other, OnlyEq)
assert_false(OnlyEq() != OnlyEq())
assert_true(OnlyEq() != 1)
# Rich comparison reflection.
class Lt:
    def __lt__(self, other): return "lt"
    def __gt__(self, other): return "gt"
assert_eq(1 < Lt(), "gt")
assert_eq(Lt() < 1, "lt")
assert_raises(TypeError, lambda: object() < object())
