# spec: PLS-315 20.3.2
# description: an attribute of a bound super object is looked up in the
# classes after __thisclass__ in __self_class__'s MRO before the super
# object's own attributes: a base's __get__, __self__ or __thisclass__,
# including property's __get__ reached by super() inside a property
# subclass's __get__, comes first; when no class has it, the super object's
# own __get__, __self__, __thisclass__ and __self_class__ answer, as they do
# for an unbound super object.
from harness import *

class A:
    __self__ = "a-self"
    __thisclass__ = "a-this"
    def __get__(self, o, t=None): return "a-get"
class B(A): pass

b = B()
s = super(B, b)
assert_eq((s.__self__, s.__thisclass__, s.__get__(1), s.__self_class__), ("a-self", "a-this", "a-get", B))

class E: pass
e = E()
t = super(E, e)
assert_eq((t.__self__ is e, t.__thisclass__, t.__self_class__, type(t.__get__(e)).__name__), (True, E, E, "super"))
u = super(E)
assert_eq((u.__self__, u.__thisclass__, u.__self_class__), (None, E, None))

class Q(property):
    def __get__(self, obj, owner=None):
        return ("q", super().__get__(obj, owner))
class C:
    @Q
    def q(self): return 2
assert_eq(C().q, ("q", 2))
assert_eq(super(Q, C.__dict__["q"]).__get__(C(), C), 2)
