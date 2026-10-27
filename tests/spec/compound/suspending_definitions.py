# spec: PLS-315 16.4, 16.5, 16.7, 27.2
# description: yield in the decorators, bases, keywords and defaults of class and function definitions, generic ones included.
from harness import *

log = []
class Meta(type):
    def __new__(mcls, name, bases, ns, **kw):
        log.append(("meta", name, bases, kw))
        return super().__new__(mcls, name, bases, ns)
def deco(tag):
    def apply(x):
        log.append(("deco", tag, x.__name__))
        return x
    return apply
class Base: pass

def g():
    @deco((yield "d1"))
    @deco("d2")
    class C(Base, (yield "base"), metaclass=Meta, flag=(yield "kw"), **(yield "map")):
        x = 1
    @deco((yield "fd"))
    def f[T](a=(yield "default"), *, b=(yield "kwdefault")) -> T:
        return a, b
    @(yield "gd")
    class G[T](Base):
        pass
    return C, f, G

it = g()
# Decorators, then bases and keywords, in source order.
assert_eq([next(it), it.send("tag1"), it.send(object), it.send(7), it.send({"extra": 8})],
          ["d1", "base", "kw", "map", "fd"])
assert_eq(log, [("meta", "C", (Base, object), {"flag": 7, "extra": 8}), ("deco", "d2", "C"), ("deco", "tag1", "C")])
# A generic function's defaults come before its type parameters exist.
assert_eq([it.send("ftag"), it.send(1), it.send(2)], ["default", "kwdefault", "gd"])
C, f, G = assert_raises(StopIteration, it.send, lambda cls: cls).value
assert_eq((C.__bases__, type(C), C.x), ((Base, object), Meta, 1))
assert_eq((f(), f.__defaults__, f.__kwdefaults__, len(f.__type_params__)), ((1, 2), (1,), {"b": 2}, 1))
assert_eq((len(G.__type_params__), G.__mro__[1]), (1, Base))

# Errors raise when the class is created, after the last resumption.
def bad():
    class D((yield), metaclass=(yield)): pass
b = bad()
next(b)
b.send(int)
assert_eq(str(assert_raises(TypeError, b.send, 5)), "'int' object is not callable")
def star():
    class E(*(yield)): pass
    return E
s = star()
next(s)
assert_eq(assert_raises(StopIteration, s.send, [Base]).value.__bases__, (Base,))

# The bases of a generic class are in its annotation scope, where yield is not allowed.
e = assert_syntax_error("def g():\n    class C[T]((yield)): pass\n")
assert_eq(e.msg, "yield expression cannot be used within the definition of a generic")
e = assert_syntax_error("def g():\n    class C[T](x=(yield)): pass\n")
assert_eq(e.msg, "yield expression cannot be used within the definition of a generic")
