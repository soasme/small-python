# spec: PLS-315 20.3.2, 20.5.2
# description: a read through a bound super object of a property, or of
# a descriptor whose class defines a Python __get__, found in a class
# after the super object's type calls the getter, which may loop, with
# super's object, or __get__ with the object, or None for a class, and
# the starting class; the getter's error propagates, an AttributeError
# with no __getattr__ of the object called, and a class's property is
# the property itself. Plain reads, method calls, getattr() and
# hasattr(), inside methods and class methods.
from harness import *

log = []

class D:
    def __get__(self, o, t):
        for _ in (): pass
        log.append((type(o).__name__, t.__name__))
        return "d"

class B:
    @property
    def p(self):
        for _ in (): pass
        log.append("p")
        return 9
    @property
    def bad(self):
        raise KeyError("bad")
    @property
    def attr(self):
        raise AttributeError("gone")
    d = D()
    def m(self): return "m"

class C(B):
    @property
    def p(self): return "own"
    def g(self): return super().p, super().d, super().m(), getattr(super(), "p"), hasattr(super(), "attr")
    @classmethod
    def k(cls): return super().d, type(super().p).__name__
    def h(self):
        try: super().bad
        except KeyError as e: return e.args
    def __getattr__(self, n): return "fallback"
    def j(self):
        try: return super().attr
        except AttributeError as e: return str(e)

assert_eq(C().g(), (9, "d", "m", 9, False))
assert_eq(log, ["p", ("C", "C"), "p"])
log.clear()
assert_eq(C.k(), ("d", "property"))
assert_eq(log, [("NoneType", "C")])
log.clear()
assert_eq((C().h(), C().j()), (("bad",), "gone"))
assert_eq((super(C, C()).p, super(C, C).d), (9, "d"))
assert_eq(log, ["p", ("NoneType", "C")])
