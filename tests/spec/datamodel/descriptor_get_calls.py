# spec: PLS-315 7.3.4, 7.3.5
# description: An instance attribute found as a class attribute whose type
# defines __get__ is that __get__'s value, called with the descriptor, the
# instance and its type; a data descriptor (one whose type defines __set__
# or __delete__) comes before the instance's own entry, which comes before
# a non-data descriptor. A class's own __getattribute__ is called with the
# name, its value or its exception the reference's, and the class's
# __getattr__ follows an AttributeError from it or from __get__, also in
# getattr() and hasattr(). Methods that loop are called inside functions
# as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class NonData:
    def __get__(self, obj, owner):
        spin(); log.append(("get", type(obj).__name__, owner.__name__))
        return "non-data"

class Data:
    def __get__(self, obj, owner):
        spin(); log.append(("data", type(obj).__name__))
        return "data"
    def __set__(self, obj, value):
        raise AttributeError("read-only")

class Deleting(NonData):
    def __delete__(self, obj): pass

class Failing:
    def __get__(self, obj, owner):
        spin()
        raise KeyError("failing")

class A:
    nd = NonData()
    d = Data()
    dl = Deleting()
    fl = Failing()

class B(A): pass

class Custom:
    def __getattribute__(self, name):
        spin(); log.append(("getattribute", name))
        if name == "missing": raise AttributeError(name)
        if name == "broken": raise ValueError(name)
        return name.upper()

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def reads():
    del log[:]
    a, b, c = A(), B(), Custom()
    a.__dict__.update(nd="own", d="own", dl="own")
    out = [a.nd, a.d, a.dl, B().nd, b.d, c.x, c.anything,
           error(lambda: A().fl), error(lambda: c.missing), error(lambda: c.broken)]
    out.append(list(log))
    return out

expected = ["own", "data", "non-data", "non-data", "data", "X", "ANYTHING",
            ("KeyError", "'failing'"), ("AttributeError", "missing"), ("ValueError", "broken"),
            [("data", "A"), ("get", "A", "A"), ("get", "B", "B"), ("data", "B"),
             ("getattribute", "x"), ("getattribute", "anything"),
             ("getattribute", "missing"), ("getattribute", "broken")]]
assert_eq(reads(), expected)
assert_eq(reads(), expected)
a = A()
assert_eq([a.nd, a.d, Custom().y], ["non-data", "data", "Y"])

# A class's __getattr__ follows an AttributeError from a descriptor's
# __get__ or the class's own __getattribute__, in a reference, getattr()
# and hasattr(); an own entry still comes before a non-data descriptor.
class Gone:
    def __get__(self, obj, owner):
        spin(); raise AttributeError("gone")

class Fallback:
    nd = NonData()
    d = Data()
    gone = Gone()
    def __getattr__(self, name):
        spin(); log.append(("getattr", name))
        return "fallback " + name

class Both(Fallback):
    def __getattribute__(self, name):
        spin(); log.append(("getattribute", name))
        if name.startswith("hidden"): raise AttributeError(name)
        return object.__getattribute__(self, name)

def fallbacks():
    del log[:]
    f, b = Fallback(), Both()
    f.__dict__["nd"] = "own"
    out = [Fallback().nd, f.nd, f.d, f.gone, getattr(f, "gone"), getattr(f, "gone", 0), hasattr(f, "gone"),
           b.hidden, getattr(b, "hidden2"), getattr(b, "hidden3", 0), b.gone]
    out.append(list(log))
    return out

assert_eq(fallbacks(), ["non-data", "own", "data", "fallback gone", "fallback gone", "fallback gone", True,
                        "fallback hidden", "fallback hidden2", "fallback hidden3", "fallback gone",
                        [("get", "Fallback", "Fallback"), ("data", "Fallback"), ("getattr", "gone"), ("getattr", "gone"),
                         ("getattr", "gone"), ("getattr", "gone"),
                         ("getattribute", "hidden"), ("getattr", "hidden"), ("getattribute", "hidden2"), ("getattr", "hidden2"),
                         ("getattribute", "hidden3"), ("getattr", "hidden3"), ("getattribute", "gone"), ("getattr", "gone")]])
