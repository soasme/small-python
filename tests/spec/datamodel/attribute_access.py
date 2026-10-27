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
