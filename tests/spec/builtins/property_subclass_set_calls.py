# spec: PLS-315 20.5.2
# description: Assigning or deleting an attribute that a property
# subclass's instance holds calls its setter or deleter, which may loop,
# once, by the statement and by setattr, an exception it raises
# propagating; without one an AttributeError names it; a subclass that
# defines __set__ calls that instead.
from harness import *

log = []
class PropertySub(property): pass
class Override(property):
    def __set__(self, obj, value):
        for _ in (): pass
        log.append(("override", value))
class Foo:
    def __init__(self): self._spam = 1
    @PropertySub
    def spam(self): return self._spam
    @spam.setter
    def spam(self, value):
        for _ in (): pass
        log.append(("set", value))
        if value == "bad": raise ValueError(value)
        self._spam = value
    @spam.deleter
    def spam(self):
        for _ in (): pass
        log.append("del")
    ro = PropertySub(lambda self: 0)
    ov = Override(lambda self: 0, lambda self, v: log.append("never"))
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
foo = Foo()
def a():
    foo.spam = 2
    return foo.spam
def b(): foo.spam = "bad"
def c(): del foo.spam
def d(): foo.ro = 1
def e(): del foo.ro
def f(): foo.ov = 3
def g():
    for i in range(2): foo.spam = i
    return foo._spam
def h(): setattr(foo, "spam", 9); return foo._spam
assert_eq([run(t) for t in (a, b, c, d, e, f, g, h)],
          [(2, [("set", 2)]), (("ValueError", "bad"), [("set", "bad")]), (None, ["del"]),
           (("AttributeError", "property 'ro' of 'Foo' object has no setter"), []),
           (("AttributeError", "property 'ro' of 'Foo' object has no deleter"), []),
           (None, [("override", 3)]), (1, [("set", 0), ("set", 1)]), (9, [("set", 9)])])
