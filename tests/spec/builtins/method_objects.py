# spec: PLS-315 28.4, 16.2.3
# description: Bound method objects: construction, calling, attribute forwarding, equality, hashing, repr.
from harness import *

class C:
    def method(self, x):
        """method doc"""
        return (self, x)
c = C()
m = c.method
MethodType = type(m)
assert_eq(MethodType.__name__, "method")
assert_is(m.__self__, c)
assert_is(m.__func__, C.method)
assert_eq(m(1), (c, 1))
assert_eq((m.__name__, m.__qualname__, m.__doc__, m.__module__), ("method", "C.method", "method doc", __name__))
C.method.extra = "forwarded"
assert_eq(m.extra, "forwarded")
e = assert_raises(AttributeError, setattr, m, "extra", 1)
assert_eq(str(e), "'method' object has no attribute 'extra' and no __dict__ for setting new attributes")
assert_eq(c.method, c.method)
assert_true(c.method is not c.method)
assert_ne(c.method, C().method)
assert_eq(hash(c.method), hash(c.method))
class Equal:
    def __eq__(self, other): return True
    __hash__ = object.__hash__
    def method(self): pass
a, b = Equal(), Equal()
assert_ne(a.method, b.method)
assert_true(repr(m).startswith("<bound method C.method of <"))
assert_is(m.__get__(None, C), m)
assert_is(m.__get__(C()), m)

made = MethodType(lambda self, y: (self, y), 5)
assert_eq(made(6), (5, 6))
assert_eq(MethodType(len, "abc")(), 3)
e = assert_raises(TypeError, MethodType, 1, c)
assert_eq(str(e), "first argument must be callable")
e = assert_raises(TypeError, MethodType, len, None)
assert_eq(str(e), "instance must not be None")
