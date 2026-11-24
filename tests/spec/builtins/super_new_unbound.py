# spec: PLS-315 20.3.2, 20.3.1
# description: super.__new__ ignores its arguments and makes a super of no
# class, which super.__init__ binds; a subclass's __new__ makes an instance
# of it. A super finds super's own attributes after the classes of its MRO.
from harness import *
class F:
    def f(self): return "F"
class G(F): pass
class mysuper(super): pass
o = G()
s = super.__new__(super, 1, 2, x=3)
assert_eq((repr(s), s.__thisclass__, s.__self__, s.__self_class__), ("<super: <class 'NULL'>, NULL>", None, None, None))
assert_raises(AttributeError, lambda: s.f)
s.__init__(G, o)
assert_eq((s.f(), s.__thisclass__ is G, s.__self__ is o), ("F", True, True))
assert_eq(type(super.__new__(mysuper)).__name__, "mysuper")
e = assert_raises(TypeError, super.__new__, int)
assert_eq(str(e), "super.__new__(int): int is not a subtype of super")
b = mysuper(G).__get__(o, G)
assert_eq((type(b).__name__, b.f()), ("mysuper", "F"))
bound = super(G, o)
assert_eq([getattr(bound, n).__self__ is bound for n in ("__init__", "__get__", "__repr__")], [False, True, False])
assert_eq((bound.__init__.__self__ is o, bound.__repr__.__self__ is o), (True, True))
