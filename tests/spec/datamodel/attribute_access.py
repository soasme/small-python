# spec: reference/datamodel.html#customizing-attribute-access
# description: __getattr__, __getattribute__, __setattr__, __delattr__, __dir__, module __getattr__.
from harness import *

class Fallback:
    x = 1
    def __getattr__(self, name):
        return "missing:" + name
f = Fallback()
assert_eq(f.x, 1)
assert_eq(f.y, "missing:y")
assert_eq(getattr(f, "z"), "missing:z")

class Logging:
    def __init__(self):
        object.__setattr__(self, "log", [])
    def __getattribute__(self, name):
        object.__getattribute__(self, "log").append(name)
        return object.__getattribute__(self, name)
    def __setattr__(self, name, value):
        self.log.append(("set", name))
        object.__setattr__(self, name, value)
    def __delattr__(self, name):
        self.log.append(("del", name))
        object.__delattr__(self, name)
l = Logging()
l.a = 1
l.a
del l.a
assert_eq(object.__getattribute__(l, "log"), ["log", ("set", "a"), "a", "log", ("del", "a")])

# __getattr__ is called when __getattribute__ raises AttributeError, including from a property.
class Prop:
    @property
    def p(self):
        raise AttributeError("inner")
    def __getattr__(self, name):
        return "fallback " + name
assert_eq(Prop().p, "fallback p")
class Other:
    @property
    def p(self):
        raise KeyError("k")
    def __getattr__(self, name):
        return "never"
assert_raises(KeyError, lambda: Other().p)

# getattr with a default swallows only AttributeError.
assert_eq(getattr(object(), "nope", 7), 7)
assert_raises(KeyError, getattr, Other(), "p", 0)
assert_false(hasattr(object(), "nope"))
assert_raises(KeyError, hasattr, Other(), "p")
assert_raises(TypeError, getattr, object(), 1)

# AttributeError carries name and obj.
o = object()
e = assert_raises(AttributeError, lambda: o.missing)
assert_eq(e.name, "missing")
assert_is(e.obj, o)

# __dir__ customizes dir(); dir() sorts the result.
class D:
    def __dir__(self):
        return ["b", "a", "c"]
assert_eq(dir(D()), ["a", "b", "c"])
class BadDir:
    def __dir__(self):
        return 5
assert_raises(TypeError, dir, BadDir())

# Instance attributes shadow non-data descriptors but not data descriptors.
class Desc:
    def __get__(self, obj, owner):
        return "desc"
class DataDesc(Desc):
    def __set__(self, obj, value):
        raise AttributeError("read-only")
class H:
    nd = Desc()
    dd = DataDesc()
h = H()
h.__dict__["nd"] = "instance"
h.__dict__["dd"] = "instance"
assert_eq(h.nd, "instance")
assert_eq(h.dd, "desc")
assert_raises(AttributeError, setattr, h, "dd", 1)

# Module __getattr__ and __dir__ (PEP 562).
import harness as module_under_test
m = type(module_under_test)("mod")
m.__getattr__ = lambda name: "lazy " + name
m.__dir__ = lambda: ["zz", "aa"]
assert_eq(m.anything, "lazy anything")
assert_eq(dir(m), ["aa", "zz"])
m2 = type(module_under_test)("mod2")
e = assert_raises(AttributeError, lambda: m2.nothing)
assert_eq(e.name, "nothing")

# Setting __class__ to a compatible class.
class P1:
    def who(self):
        return 1
class P2:
    def who(self):
        return 2
p = P1()
p.__class__ = P2
assert_eq(p.who(), 2)
assert_raises(TypeError, setattr, p, "__class__", int)
assert_raises(TypeError, setattr, 1, "__class__", bool)
# SetAttr on objects without a namespace: a member descriptor is a
# "readonly attribute", a getset is "not writable", and another class
# attribute, __doc__ included, is read-only.
def set_error(obj, name, delete=False):
    with_value = (lambda: delattr(obj, name)) if delete else (lambda: setattr(obj, name, 1))
    return str(assert_raises(AttributeError, with_value))
code = (lambda: 0).__code__
for obj, name, message in (
        (1j, "real", "readonly attribute"), (slice(1), "stop", "readonly attribute"),
        (code, "co_name", "readonly attribute"), (code, "co_varnames", "attribute 'co_varnames' of 'code' objects is not writable"),
        (True, "real", "attribute 'real' of 'int' objects is not writable"),
        (memoryview(b"a"), "nbytes", "attribute 'nbytes' of 'memoryview' objects is not writable"),
        (t"a{1}".interpolations[0], "value", "readonly attribute"), (t"a", "strings", "readonly attribute"),
        ((1).__add__, "__self__", "readonly attribute"), (list.append, "__name__", "readonly attribute"),
        (list.append, "__qualname__", "attribute '__qualname__' of 'method_descriptor' objects is not writable"),
        (len, "__name__", "attribute '__name__' of 'builtin_function_or_method' objects is not writable"),
        (5, "__doc__", "'int' object attribute '__doc__' is read-only"),
        (object(), "__doc__", "'object' object attribute '__doc__' is read-only"),
        ([], "append", "'list' object attribute 'append' is read-only")):
    assert_eq(set_error(obj, name), message)
    assert_eq(set_error(obj, name, True), message)
# Function attributes refuse deletion as they refuse a wrong type.
def function(): pass
for name, message in (("__name__", "__name__ must be set to a string object"),
                      ("__qualname__", "__qualname__ must be set to a string object"),
                      ("__code__", "__code__ must be set to a code object"),
                      ("__type_params__", "__type_params__ must be set to a tuple"),
                      ("__dict__", "cannot delete __dict__")):
    assert_eq(str(assert_raises(TypeError, delattr, function, name)), message)
assert_eq(str(assert_raises(TypeError, setattr, function, "__name__", 1)), "__name__ must be set to a string object")
class Text(str): pass
function.__name__ = Text("renamed")
assert_eq(function.__name__, "renamed")
assert_eq(str(assert_raises(TypeError, setattr, function, "__dict__", 1)), "__dict__ must be set to a dictionary, not a 'int'")
assert_eq(str(assert_raises(TypeError, setattr, function, "__class__", 1)), "__class__ must be set to a class, not 'int' object")
assert_eq(str(assert_raises(TypeError, delattr, staticmethod(len), "__dict__")), "cannot delete __dict__")
assert_eq(str(assert_raises(TypeError, delattr, ValueError(), "__dict__")), "cannot delete __dict__")
error = UnicodeDecodeError("utf-8", b"", 0, 1, "reason")
assert_eq(str(assert_raises(TypeError, delattr, error, "start")), "can't delete numeric/char attribute")
error.end = True
assert_eq((type(error.end), error.end), (int, 1))
