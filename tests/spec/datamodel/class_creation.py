# spec: reference/datamodel.html#customizing-class-creation
# description: __init_subclass__, __set_name__, metaclasses, __prepare__, __class_getitem__, __mro_entries__.
from harness import *

log = []
class Base:
    def __init_subclass__(cls, /, tag=None, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.tag = tag
        log.append(cls.__name__)
class Child(Base, tag="x"): pass
assert_eq(Child.tag, "x")
assert_eq(log, ["Child"])
assert_true(isinstance(Base.__dict__["__init_subclass__"], classmethod))
assert_raises(TypeError, run, "class C(object, bogus=1): pass")

class Named:
    def __set_name__(self, owner, name):
        self.owner, self.name = owner, name
class Holder:
    attr = Named()
assert_eq(Holder.attr.name, "attr")
assert_is(Holder.attr.owner, Holder)

order = []
class Meta(type):
    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        order.append(("prepare", name, kwargs))
        return {"injected": 1}
    def __new__(mcs, name, bases, namespace, **kwargs):
        order.append(("new", sorted(k for k in namespace if not k.startswith("__"))))
        return super().__new__(mcs, name, bases, namespace)
    def __init__(cls, name, bases, namespace, **kwargs):
        order.append(("init", name))
        super().__init__(name, bases, namespace)
    def __call__(cls, *args):
        order.append(("call", args))
        return super().__call__(*args)
class M(metaclass=Meta, flag=True):
    x = injected + 1
assert_eq(order[0], ("prepare", "M", {"flag": True}))
assert_eq(order[1], ("new", ["injected", "x"]))
assert_eq(order[2], ("init", "M"))
M()
assert_eq(order[3], ("call", ()))
assert_is(type(M), Meta)
class Sub(M): pass
assert_is(type(Sub), Meta)

# The most derived metaclass wins; unrelated metaclasses conflict.
class Meta2(type): pass
class N(metaclass=Meta2): pass
assert_raises(TypeError, run, "class X(M, N): pass", {"M": M, "N": N})
class Meta3(Meta, Meta2): pass
class Y(M, metaclass=Meta3): pass
assert_is(type(Y), Meta3)

# __class__ cell and __classcell__ propagation.
class WithCell:
    def f(self): return __class__
assert_is(WithCell().f(), WithCell)

class Generic:
    def __class_getitem__(cls, item):
        return (cls, item)
assert_eq(Generic[int], (Generic, int))
assert_eq(list[int].__origin__, list)

class Entries:
    def __mro_entries__(self, bases):
        return (dict,)
class FromEntries(Entries()): pass
assert_eq(FromEntries.__bases__, (dict,))
assert_eq(FromEntries.__orig_bases__[0].__class__, Entries)

# type(name, bases, dict) builds a class; type(x) returns its type.
T = type("T", (Base,), {"v": 3})
assert_eq((T.__name__, T.v, T.tag), ("T", 3, None))
assert_is(type(3), int)
assert_raises(TypeError, type, "T", 1, {})
# The class body runs in order and its namespace is ordered.
class Ordered:
    b = 1
    a = 2
assert_eq([k for k in Ordered.__dict__ if not k.startswith("__")], ["b", "a"])
assert_eq(Ordered.__qualname__, "Ordered")
def outer():
    class Inner: pass
    return Inner
assert_eq(outer().__qualname__, "outer.<locals>.Inner")
