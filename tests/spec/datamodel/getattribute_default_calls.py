# spec: PLS-315 7.3.4, 7.3.6
# description: object.__getattribute__(obj, name) and
# type.__getattribute__(cls, name), called explicitly, unbound, through
# super() or a base found in the MRO, read the attribute by the default
# lookup: a property's getter or a data descriptor's __get__ before the
# instance's own entry, an own entry before a non-data descriptor, a class
# attribute's __get__ with None and the class, a metaclass property before
# the class's own attribute; each getter may loop, its value or exception
# the call's, and the class's __getattr__ runs only after an AttributeError
# leaves the class's own __getattribute__. A str subclass names the
# attribute; a name that is not a str raises TypeError. Inside functions as
# at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class NonData:
    def __get__(self, obj, owner):
        spin(); log.append(("nondata", obj is None, owner.__name__))
        return "nondata"

class Data(NonData):
    def __get__(self, obj, owner):
        spin(); log.append(("data", obj is None, owner.__name__))
        return "data"
    def __set__(self, obj, value): pass

class Name(str): pass

class Base:
    nd = NonData()
    dd = Data()
    shadow = NonData()
    @property
    def p(self):
        spin(); log.append("p")
        return "p"
    @property
    def gone(self):
        spin(); log.append("gone")
        raise AttributeError("gone inside")
    @property
    def bad(self):
        spin()
        raise KeyError("bad")

class A(Base):
    def __init__(self):
        self.__dict__.update(dd="own dd", shadow="own shadow")
    def __getattribute__(self, name):
        log.append(("ga", name))
        return object.__getattribute__(self, name)
    def __getattr__(self, name):
        spin(); log.append(("fallback", name))
        return "fallback " + name

class S(Base):
    def __getattribute__(self, name):
        return super().__getattribute__(name)

class Meta(type):
    @property
    def mp(cls):
        spin(); log.append(("mp", cls.__name__))
        return "mp"
    def __getattribute__(cls, name):
        return type.__getattribute__(cls, name)

class K(metaclass=Meta):
    nd = NonData()
    mp = "own mp"

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def reads():
    del log[:]
    a, s = A(), S()
    out = [a.p, a.nd, a.dd, a.shadow, a.gone, a.missing, error(lambda: a.bad)]
    out += [s.p, s.nd, error(lambda: s.gone), object.__getattribute__(a, Name("p")), Base.__getattribute__(a, "nd"),
            type(a).__mro__[1].__getattribute__(a, "dd"), error(lambda: object.__getattribute__(a, "gone")),
            error(lambda: object.__getattribute__(a, 1))]
    out += [K.mp, K.nd, type.__getattribute__(K, "nd"), error(lambda: type.__getattribute__(K, "absent"))]
    out.append(list(log))
    return out

expected = ["p", "nondata", "data", "own shadow", "fallback gone", "fallback missing", ("KeyError", "'bad'"),
            "p", "nondata", ("AttributeError", "gone inside"), "p", "nondata", "data", ("AttributeError", "gone inside"),
            ("TypeError", "attribute name must be string, not 'int'"),
            "mp", "nondata", "nondata", ("AttributeError", "type object 'K' has no attribute 'absent'"),
            [("ga", "__dict__"), ("ga", "p"), "p", ("ga", "nd"), ("nondata", False, "A"), ("ga", "dd"), ("data", False, "A"), ("ga", "shadow"),
             ("ga", "gone"), "gone", ("fallback", "gone"), ("ga", "missing"), ("fallback", "missing"), ("ga", "bad"),
             "p", ("nondata", False, "S"), "gone", "p", ("nondata", False, "A"), ("data", False, "A"), "gone",
             ("mp", "K"), ("nondata", True, "K"), ("nondata", True, "K")]]

def main():
    return reads()

assert_eq(main(), expected)
assert_eq(reads(), expected)
