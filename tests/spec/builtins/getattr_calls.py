# spec: PLS-315 19.3.13, 7.2.1
# description: getattr(object, name) reads the attribute as attribute
# syntax does: a property's getter, a descriptor's __get__, a class's own
# __getattribute__, or __getattr__ after an AttributeError, each of which
# may loop, inside functions as at module level. An AttributeError raised
# there propagates with its name and obj filled in, a getter's to
# __getattr__; a str subclass names the attribute, and a default answers
# an AttributeError.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Descriptor:
    def __get__(self, obj, owner):
        spin()
        log.append(("get", type(obj).__name__, owner.__name__))
        return "described"

class Thing:
    d = Descriptor()
    def __init__(self): self.own = "own"
    @property
    def p(self):
        spin()
        log.append("p")
        return "property"
    @property
    def broken(self):
        spin()
        raise AttributeError("inner")
    def __getattr__(self, name):
        spin()
        log.append(("getattr", name))
        if name == "absent":
            raise AttributeError("no " + name)
        return name.upper()

class Guarded:
    def __getattribute__(self, name):
        spin()
        log.append(("getattribute", name))
        if name == "secret":
            raise AttributeError(name)
        return "guarded " + name

class Plain:
    pass

class Name(str): pass

def failure(f):
    try:
        f()
    except AttributeError as e:
        return str(e), e.name, type(e.obj).__name__

def reads():
    del log[:]
    t, g = Thing(), Guarded()
    out = [getattr(t, "p"), getattr(t, "own"), getattr(t, "d"), getattr(t, "dynamic"), getattr(g, "any")]
    out.append(failure(lambda: getattr(t, "absent")))
    out.append(failure(lambda: getattr(g, "secret")))
    out.append(failure(lambda: getattr(Plain(), "missing")))
    out.append(failure(lambda: getattr(t, "broken")))
    out += [getattr(t, Name("p")), getattr(Plain(), "missing", "default"), getattr(t, "absent", "default")]
    items = []
    items.append(getattr(t, "p"))
    out.append(items)
    out.append(list(log))
    return out

def shadowed():
    getattr = lambda *args: "shadow"
    return getattr(Thing(), "p")

expected = ["property", "own", "described", "DYNAMIC", "guarded any",
            ("no absent", "absent", "Thing"),
            ("secret", "secret", "Guarded"),
            ("'Plain' object has no attribute 'missing'", "missing", "Plain"),
            None,
            "property", "default", "default", ["property"],
            ["p", ("get", "Thing", "Thing"), ("getattr", "dynamic"), ("getattribute", "any"),
             ("getattr", "absent"), ("getattribute", "secret"), ("getattr", "broken"), "p", ("getattr", "absent"), "p"]]

def main():
    return reads()

assert_eq(main(), expected)
assert_eq(reads(), expected)
assert_eq(shadowed(), "shadow")
