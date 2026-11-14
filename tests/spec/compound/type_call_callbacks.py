# spec: PLS-315 16.4.2, 16.4.3
# description: type() of a name, bases and a namespace, and type.__new__
# called from a metaclass's __new__ (directly, through super(), or with
# keywords), finish the class as a class statement does: each namespace
# value's Python __set_name__ in definition order, then the base's Python
# __init_subclass__ with the keywords, each of which may loop, before the
# call returns the class; a __set_name__ error gains its note and stops the
# rest, an __init_subclass__ error propagates from the call. Inside
# functions as at module level.
from harness import *

log = []

class Named:
    def __init__(self, tag): self.tag = tag
    def __set_name__(self, owner, name):
        for _ in (): pass
        log.append(("set", self.tag, owner.__name__, name))
        if self.tag == "bad": raise LookupError(name)

class Base:
    def __init_subclass__(cls, **kw):
        for _ in (): pass
        log.append(("sub", cls.__name__, kw))
        if kw.get("fail"): raise KeyError("sub")

class Meta(type):
    def __new__(mcls, name, bases, ns, **kw):
        for _ in (): pass
        log.append(("new", name))
        if kw.pop("direct", False): return type.__new__(mcls, name, bases, ns, **kw)
        return super().__new__(mcls, name, bases, ns, **kw)

def makes():
    out = []
    A = type("A", (Base,), {"x": Named(1), "y": 2, "z": Named(2)})
    out.append((A.__name__, log[:])); log.clear()
    B = type("B", (Base,), {"x": Named(3)}, k=1)
    out.append((B.__name__, log[:])); log.clear()
    class C(Base, metaclass=Meta, k=2):
        x = Named(4)
    out.append((type(C).__name__, log[:])); log.clear()
    class D(Base, metaclass=Meta, direct=True):
        x = Named(5)
    out.append((type(D).__name__, log[:])); log.clear()
    E = type.__new__(Meta, "E", (Base,), {"x": Named(6)})
    out.append((type(E).__name__, log[:])); log.clear()
    ns = {"x": Named(7)}
    F = type("F", (), ns)
    out.append((F.__name__, log[:])); log.clear()
    return out

assert_eq(makes(), [
    ("A", [("set", 1, "A", "x"), ("set", 2, "A", "z"), ("sub", "A", {})]),
    ("B", [("set", 3, "B", "x"), ("sub", "B", {"k": 1})]),
    ("Meta", [("new", "C"), ("set", 4, "C", "x"), ("sub", "C", {"k": 2})]),
    ("Meta", [("new", "D"), ("set", 5, "D", "x"), ("sub", "D", {})]),
    ("Meta", [("set", 6, "E", "x"), ("sub", "E", {})]),
    ("F", [("set", 7, "F", "x")]),
])

def errors():
    out = []
    try: type("G", (Base,), {"a": Named("bad"), "b": Named(8)})
    except LookupError as e: out.append((e.args, e.__notes__, log[:]))
    log.clear()
    try: type("H", (Base,), {"a": Named(9)}, fail=True)
    except KeyError as e: out.append((e.args, log[:]))
    log.clear()
    try: type("I", (Base,), {}, fail=True, extra=1)
    except KeyError as e: out.append(e.args)
    log.clear()
    return out

assert_eq(errors(), [
    (("a",), ["Error calling __set_name__ on 'Named' instance 'a' in 'G'"], [("set", "bad", "G", "a")]),
    (("sub",), [("set", 9, "H", "a"), ("sub", "H", {"fail": True})]),
    ("sub",),
])
