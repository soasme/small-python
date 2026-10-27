# spec: PLS-315 20.6, 20.7, 28.4
# description: staticmethod and classmethod descriptors, their copied attributes, and binding.
from harness import *

def f(*args):
    """doc of f"""
    return args
f.__annotations__ = {"return": int}
s = staticmethod(f)
assert_is(s.__get__(None, object), f)
assert_is(s.__get__(1, int), f)
assert_eq(s(1, 2), (1, 2))
assert_eq((s.__name__, s.__qualname__, s.__doc__, s.__module__), ("f", "f", "doc of f", __name__))
assert_eq(s.__annotations__, {"return": int})
assert_is(s.__func__, f)
assert_is(s.__wrapped__, f)
assert_false(s.__isabstractmethod__)

class C:
    @staticmethod
    def sm(x):
        return ("static", x)
    @classmethod
    def cm(cls, x):
        return (cls, x)
class D(C):
    pass
assert_eq(C.sm(1), ("static", 1))
assert_eq(C().sm(1), ("static", 1))
assert_eq(C.cm(1), (C, 1))
assert_eq(C().cm(1), (C, 1))
assert_eq(D.cm(1), (D, 1))
assert_eq(D().cm(1), (D, 1))
bound = C.cm
assert_is(bound.__self__, C)
assert_is(bound.__func__, C.__dict__["cm"].__func__)
c = classmethod(f)
# __get__ with owner None binds to the instance's type.
assert_is(c.__get__(5).__self__, int)
assert_is(c.__get__(5, None).__self__, int)
assert_is(c.__get__(None, str).__self__, str)
assert_eq(c.__get__(None, str)(1), (str, 1))
assert_eq((c.__name__, c.__doc__), ("f", "doc of f"))
assert_is(c.__wrapped__, f)
assert_eq(c.__annotations__, {"return": int})
# classmethod does not call the wrapped object's __get__.
class Descriptor:
    def __get__(self, instance, owner):
        fail("classmethod called __get__")
    def __call__(self, *args):
        return args
wrapped = classmethod(Descriptor())
assert_eq(wrapped.__get__(None, int)(2), (int, 2))
# __isabstractmethod__ reflects the function's.
def abstract(): pass
abstract.__isabstractmethod__ = True
assert_true(staticmethod(abstract).__isabstractmethod__)
assert_true(classmethod(abstract).__isabstractmethod__)
# A staticmethod of a non-callable is created but fails when called.
assert_raises(TypeError, staticmethod(1))
assert_eq(repr(staticmethod(f)).startswith("<staticmethod("), True)
assert_eq(repr(classmethod(f)).startswith("<classmethod("), True)
