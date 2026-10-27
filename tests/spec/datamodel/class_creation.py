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

# type() takes one or three arguments; __classcell__ must be a cell.
assert_raises(TypeError, type, 1, 2, message="type() takes 1 or 3 arguments")
e = assert_raises(TypeError, type, "X", (), {"__classcell__": 1})
assert_eq(str(e), "__classcell__ must be a nonlocal cell, not <class 'int'>")

# __class__ can be assigned between classes adding the same slots, though
# instances have no __dict__; a __dict__ slot over a base that has one is
# refused before any class variable conflict.
class SameA:
    __slots__ = ("x",)
class SameB:
    __slots__ = ("x",)
class Other:
    __slots__ = ("y",)
same = SameA()
same.__class__ = SameB
assert_true(type(same) is SameB)
assert_raises(TypeError, setattr, same, "__class__", Other)
class HasDict:
    pass
try:
    type("Clash", (HasDict,), {"__slots__": ("a", "__dict__"), "a": 0})
except TypeError as error:
    assert_eq(str(error), "__dict__ slot disallowed: we already got one")

# A method using __class__ or super() gets a __classcell__ that type.__new__ fills.
seen = []
class CellMeta(type):
    def __new__(meta, name, bases, namespace):
        seen.append(type(namespace.get("__classcell__")).__name__)
        if name == "Dropped":
            namespace = {k: v for k, v in namespace.items() if k != "__classcell__"}
        return super().__new__(meta, name, bases, namespace)
class Uses(metaclass=CellMeta):
    def f(self):
        return __class__
class Unused(metaclass=CellMeta):
    def f(self):
        return 1
assert_eq(seen, ["cell", "NoneType"])
assert_true(Uses().f() is Uses)
assert_true("__classcell__" not in Uses.__dict__)
def dropped():
    class Dropped(metaclass=CellMeta):
        def f(self):
            return super()
e = assert_raises(RuntimeError, dropped)
assert_true(str(e).startswith("__class__ not set defining 'Dropped' as <class '"))

# Annotated names cannot be declared global or nonlocal.
for source, message in [("def f():\n    global x\n    x: int = 1", "annotated name 'x' can't be global"),
                        ("def f():\n    x: int\n    global x", "annotated name 'x' can't be global"),
                        ("def g():\n    x = 1\n    def f():\n        nonlocal x\n        x: int", "annotated name 'x' can't be nonlocal"),
                        ("def g():\n    x = 1\n    def f():\n        nonlocal x\n        global x", "name 'x' is nonlocal and global")]:
    e = assert_raises(SyntaxError, compile, source, "<scope>", "exec")
    assert_eq(e.msg, message)
e = assert_raises(SyntaxError, compile, "def g():\n    x = 1\n    def f():\n        nonlocal x\n        global x", "<scope>", "exec")
assert_eq(e.lineno, 4)
compile("global x\nx: int = 1", "<scope>", "exec")
