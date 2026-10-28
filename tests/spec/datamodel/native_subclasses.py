# spec: PLS-315 27.1, 20.3, 17.2, 10.1.3
# description: Subclasses of map, zip, enumerate, filter, reversed, super, and module, and assigning a module's __class__.
from harness import *

ModuleType = type(__build_class__.__self__)

# Iterator subclasses are their own iterators; overriding __next__ applies.
class M(map):
    def __next__(self): return ("M", super().__next__())
assert_eq(list(M(abs, [-1, -2])), [("M", 1), ("M", 2)])
assert_eq((type(M(abs, [])).__name__, isinstance(M(abs, []), map), M.__mro__), ("M", True, (M, map, object)))
class Z(zip):
    extra = 1
z = Z("ab", [1, 2])
assert_eq((iter(z) is z, next(z), list(z), Z("a", "b").extra), (True, ("a", 1), [("b", 2)], 1))
assert_eq(str(assert_raises(ValueError, list, Z("ab", [1], strict=True))), "zip() argument 2 is shorter than argument 1")
class E(enumerate):
    def __new__(cls, iterable, start=0):
        self = super().__new__(cls, iterable, start)
        self.tag = "t"
        return self
assert_eq((list(E("xy", 5)), E("q").tag), ([(5, "x"), (6, "y")], "t"))
class F(filter): pass
assert_eq(list(F(None, [0, 1, 2])), [1, 2])
f = F(None, [3])
f.attr = 4
assert_eq((f.attr, next(f), next(f, "done")), (4, 3, "done"))
# reversed() returns what an object's __reversed__ returns, whatever the class.
class R(reversed):
    def __length_hint__(self): return 99
assert_eq((list(R([1, 2, 3])), type(R([1])).__name__), ([3, 2, 1], "list_reverseiterator"))
class Seq:
    def __len__(self): return 2
    def __getitem__(self, i): return "ab"[i]
r = R(Seq())
assert_eq((type(r) is R, r.__length_hint__(), list(r)), (True, 99, ["b", "a"]))
assert_eq(str(assert_raises(TypeError, map.__new__, int)), "map.__new__(int): int is not a subtype of map")

# A super subclass looks up past its __thisclass__ like super.
class S(super):
    def __getattribute__(self, name):
        return ("S", super().__getattribute__(name))
class A:
    def f(self): return "A.f"
class B(A):
    def f(self): return S(B, self).f
tag, method = B().f()
assert_eq((tag, method()), ("S", "A.f"))
class S2(super): pass
class C(A):
    def f(self): return S2(C, self).f()
assert_eq(C().f(), "A.f")
s = S2(C, C())
assert_eq((type(s).__name__, isinstance(s, super), s.__thisclass__), ("S2", True, C))

# A module subclass's instance has the module's namespace as its __dict__.
class Mod(ModuleType):
    def __init__(self, name, extra):
        super().__init__(name)
        self.extra = extra
    @property
    def prop(self): return "p:" + self.__name__
m = Mod("mname", 5)
assert_eq((m.__name__, m.extra, m.prop, m.__doc__), ("mname", 5, "p:mname", None))
assert_eq(sorted(m.__dict__), ["__doc__", "__loader__", "__name__", "__package__", "__spec__", "extra"])
assert_eq((repr(m), m.__dict__ is vars(m), isinstance(m, ModuleType), type(m) is Mod), ("<module 'mname'>", True, True, True))
del m.extra
assert_eq("extra" in m.__dict__, False)
assert_eq(str(assert_raises(AttributeError, lambda: m.nope)), "module 'mname' has no attribute 'nope'")
assert_eq([name for name in dir(m) if not name.startswith("__")], [])
assert_eq(str(assert_raises(AttributeError, setattr, m, "prop", 1)), "property 'prop' of 'Mod' object has no setter")
class Plain(ModuleType): pass
assert_eq((Plain("q").__name__, repr(Plain("q", "d")), Plain("q", "d").__doc__), ("q", "<module 'q'>", "d"))
assert_eq(str(assert_raises(TypeError, Plain)), "module() missing required argument 'name' (pos 1)")
p = Plain("a")
ModuleType.__init__(p, "b", "docb")
assert_eq((p.__name__, p.__doc__), ("b", "docb"))

# A module's __class__ may be set to any ModuleType subclass and back.
x = ModuleType("x")
x.v = 1
x.__class__ = Plain
assert_eq((type(x).__name__, x.v, x.__name__, isinstance(x, Plain)), ("Plain", 1, "x", True))
x.__class__ = ModuleType
assert_eq((type(x).__name__, x.v), ("module", 1))
class Lazy(ModuleType):
    def __getattr__(self, name): return name * 2
x.__class__ = Lazy
assert_eq((x.ab, x.v), ("abab", 1))
e = assert_raises(TypeError, setattr, x, "__class__", int)
assert_eq(str(e), "__class__ assignment only supported for mutable types or ModuleType subclasses")
