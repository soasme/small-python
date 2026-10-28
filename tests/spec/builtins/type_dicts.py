# spec: PLS-315 10.1.3, 19.3.6, 28.5, 16.2.1
# description: The data descriptors that built-in type dictionaries hold for instance fields, and dir() listing them.
from harness import *

class A:
    pass
class B:
    pass

# object.__dict__["__class__"] is the data descriptor of 10.1.3.
d = object.__dict__["__class__"]
assert_eq(type(d).__name__, "getset_descriptor")
a = A()
assert_is(d.__get__(a), A)
d.__set__(a, B)
assert_is(type(a), B)
e = assert_raises(TypeError, d.__delete__, a)
assert_eq(str(e), "can't delete __class__ attribute")
assert_is(A.__class__, type)
for value in (object(), 1, "s", [], A(), A, None, len, (lambda: 0), iter(()), 1.5):
    assert_true("__class__" in dir(value), type(value).__name__)

# Fields spelt like the type's own __name__ and __qualname__.
def f():
    pass
function = type(f)
assert_eq(function.__name__, "function")
assert_eq(function.__dict__["__name__"].__get__(f), "f")
assert_eq(type(function.__dict__["__qualname__"]).__name__, "getset_descriptor")
assert_eq(type(len).__dict__["__name__"].__get__(len), "len")
assert_eq(type(type(len).__dict__["__module__"]).__name__, "member_descriptor")
gen = (x for x in ())
assert_eq(type(gen).__dict__["__name__"].__get__(gen), "<genexpr>")
for value, names in ((f, ("__name__", "__qualname__", "__module__")), (len, ("__name__", "__qualname__", "__self__", "__text_signature__")),
                     (f.__call__, ("__call__", "__name__", "__qualname__", "__self__", "__objclass__", "__text_signature__")),
                     (object.__repr__, ("__call__", "__name__", "__objclass__", "__text_signature__")),
                     (str.join, ("__call__", "__name__", "__qualname__", "__objclass__")), (gen, ("__name__", "__qualname__")),
                     (property(), ("__name__",)), (None, ("__bool__",))):
    for name in names:
        assert_true(name in dir(value), (type(value).__name__, name))
a = A()
assert_eq(object.__repr__.__call__(a), object.__repr__(a))
assert_eq(str.join.__call__("-", "ab"), "a-b")
assert_is(None.__bool__(), False)
