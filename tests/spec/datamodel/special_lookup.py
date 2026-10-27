# spec: PLS-315 7.3.2
# description: Implicit special method calls look up the type, bypassing the instance and __getattribute__.
from harness import *

class C:
    pass
c = C()
c.__len__ = lambda: 5
assert_raises(TypeError, len, c)
assert_eq(c.__len__(), 5)

class Meta(type):
    def __getattribute__(cls, name):
        Meta.log.append(name)
        return type.__getattribute__(cls, name)
Meta.log = []
class D(metaclass=Meta):
    def __len__(self):
        return 10
    def __getattribute__(self, name):
        raise AssertionError("instance __getattribute__ must not be used for " + name)
d = D()
Meta.log.clear()
assert_eq(len(d), 10)
assert_eq(Meta.log, [])

# Special methods defined on the metaclass apply to the class itself.
class LenMeta(type):
    def __len__(cls):
        return 3
class E(metaclass=LenMeta):
    def __len__(self):
        return 7
assert_eq(len(E), 3)
assert_eq(len(E()), 7)

# Replacing a special method on the class takes effect immediately.
class F:
    def __repr__(self):
        return "one"
f = F()
assert_eq(repr(f), "one")
F.__repr__ = lambda self: "two"
assert_eq(repr(f), "two")
del F.__repr__
assert_true(repr(f).startswith("<"))

# Setting a special method to None blocks the operation.
class NoIter:
    __iter__ = None
    def __getitem__(self, i):
        return i
assert_raises(TypeError, iter, NoIter())
class NoHash:
    __hash__ = None
assert_raises(TypeError, hash, NoHash())
class NoContains:
    __contains__ = None
    def __iter__(self):
        return iter([1])
assert_raises(TypeError, lambda: 1 in NoContains())
class NoReversed:
    __reversed__ = None
    def __len__(self):
        return 1
    def __getitem__(self, i):
        return i
assert_raises(TypeError, reversed, NoReversed())

# Descriptors (staticmethod, classmethod, property) work as special methods.
class G:
    @staticmethod
    def __len__():
        raise AssertionError
    __len__ = lambda self: 4
    __bool__ = property(lambda self: lambda: False) if False else (lambda self: False)
assert_eq(len(G()), 4)
assert_false(G())

# A metaclass supplies its classes' operators and attribute hooks: unary
# operators, abs(), format(), item assignment and deletion, divmod(), pow()
# with a modulus, next(), __getattribute__, and __getattr__.
class OpsMeta(type):
    store = {}
    looked = []
    def __neg__(cls): return "neg"
    def __abs__(cls): return "abs"
    def __format__(cls, spec): return "fmt" + spec
    def __setitem__(cls, key, value): OpsMeta.store[key] = value
    def __delitem__(cls, key): del OpsMeta.store[key]
    def __divmod__(cls, other): return "divmod"
    def __pow__(cls, other, modulus=None): return ("pow", modulus)
    def __next__(cls): return "next"
    def __getattr__(cls, name): return "missing " + name
    def __getattribute__(cls, name):
        OpsMeta.looked.append(name)
        return type.__getattribute__(cls, name)
class Ops(metaclass=OpsMeta):
    pass
assert_eq((-Ops, abs(Ops), format(Ops, "x"), divmod(Ops, 1), pow(Ops, 2, 5), next(Ops)),
          ("neg", "abs", "fmtx", "divmod", ("pow", 5), "next"))
Ops["k"] = 1
assert_eq(OpsMeta.store, {"k": 1})
del Ops["k"]
assert_eq(OpsMeta.store, {})
OpsMeta.looked.clear()
assert_eq(Ops.nope, "missing nope")
assert_eq(OpsMeta.looked, ["nope"])
class Plain:
    pass
try:
    del Plain[1]
except TypeError as error:
    assert_eq(str(error), "'type' object does not support item deletion")
