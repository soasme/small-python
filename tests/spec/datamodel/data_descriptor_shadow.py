# spec: PLS-315 7.3.4, 7.3.5
# description: A class attribute whose type defines __get__ and __set__ or
# __delete__ is read through its __get__ even when the instance's __dict__
# holds an entry of the same name, while a descriptor with only __get__
# yields to that entry; __get__ may loop, an exception from it propagates,
# and getattr() with a default gives the default only for an
# AttributeError, inside functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Data:
    def __get__(self, obj, owner):
        spin(); log.append(("data", type(obj).__name__))
        if getattr(obj, "fail", None): raise obj.fail
        return "data"
    def __set__(self, obj, value): pass

class Deleting:
    def __get__(self, obj, owner):
        spin(); log.append("deleting")
        return "deleting"
    def __delete__(self, obj): pass

class NonData:
    def __get__(self, obj, owner):
        spin(); log.append("non-data")
        return "non-data"

class A:
    d = Data()
    dl = Deleting()
    nd = NonData()

class B(A): pass

def shadowed(cls):
    a = cls()
    a.__dict__.update(d="own", dl="own", nd="own")
    return a

def reads():
    del log[:]
    a, b = shadowed(A), shadowed(B)
    out = [a.d, a.dl, a.nd, b.d, getattr(a, "d"), getattr(b, "dl", 0), getattr(a, "nd", 0)]
    a.fail = KeyError("k")
    out.append(error(lambda: a.d))
    out.append(error(lambda: getattr(a, "d", 0)))
    a.fail = AttributeError("gone")
    out.append(getattr(a, "d", 0))
    out.append(list(log))
    return out

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

expected = ["data", "deleting", "own", "data", "data", "deleting", "own",
            ("KeyError", "'k'"), ("KeyError", "'k'"), 0,
            [("data", "A"), "deleting", ("data", "B"), ("data", "A"), "deleting",
             ("data", "A"), ("data", "A"), ("data", "A")]]
assert_eq(reads(), expected)
assert_eq(reads(), expected)
a = shadowed(A)
log.clear()
assert_eq([a.d, a.dl, a.nd, getattr(a, "d", 0)], ["data", "deleting", "own", "data"])
assert_eq(log, [("data", "A"), "deleting", ("data", "A")])
