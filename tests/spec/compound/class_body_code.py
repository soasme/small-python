# spec: PLS-315 16.4.2, 16.4.3, 9.3.3, 28.1, 28.2
# description: The code of a class body: its __classdict__ and __class__ cells, the class dictionary cell type.__new__ fills, and functions made from it.
from harness import *

FunctionType = type(lambda: None)
CellType = type((lambda x: lambda: x)(0).__closure__[0])

# A __build_class__ that keeps each body function it is given.
captured = []
def builder(func, name, *bases, **kw):
    captured.append(func)
    return __build_class__(func, name, *bases, **kw)
def bodies(source, namespace=None):
    del captured[:]
    namespace = namespace if namespace is not None else {}
    namespace.setdefault("__name__", "src")
    namespace["__builtins__"] = dict(vars(__build_class__.__self__), __build_class__=builder)
    exec(source, namespace)
    return [f.__code__ for f in captured]

# co_cellvars: __classdict__ when a scope in the body can see the class namespace.
cases = [
    ("class C:\n    x = 1\n", ()),
    ("class C:\n    'doc'\n", ()),
    ("class C:\n    f = lambda: 0\n", ()),
    ("class C:\n    x = [i for i in ()]\n", ()),
    ("class C:\n    x = (i for i in ())\n", ()),
    ("class C:\n    def m(self): pass\n", ("__classdict__",)),
    ("class C:\n    async def m(self): pass\n", ("__classdict__",)),
    ("class C:\n    if 1:\n        def m(self): pass\n", ("__classdict__",)),
    ("class C:\n    try:\n        def m(self): pass\n    except: pass\n", ("__classdict__",)),
    ("class C:\n    @staticmethod\n    def m(): pass\n", ("__classdict__",)),
    ("class C:\n    x: int\n", ("__classdict__",)),
    ("class C:\n    x: int = 1\n", ("__classdict__",)),
    ("class C:\n    (x): int\n", ("__classdict__",)),
    ("class C:\n    type A = int\n", ("__classdict__",)),
    ("class C:\n    def m(self): return __class__\n", ("__class__", "__classdict__")),
    ("class C:\n    def m(self): return super()\n", ("__class__", "__classdict__")),
]
for source, cells in cases:
    code = bodies(source)[0]
    assert_eq((code.co_name, code.co_cellvars, code.co_freevars, code.co_argcount), ("C", cells, (), 0), source)
# A nested class's scopes belong to its own body.
outer, inner = bodies("class C:\n    class D:\n        x: int\n        def m(self): return __class__\n")
assert_eq((outer.co_name, outer.co_cellvars, inner.co_name, inner.co_cellvars), ("C", (), "D", ("__class__", "__classdict__")))

# co_freevars: the names a class body uses from enclosing functions, sorted.
free_cases = [
    ("def f(a):\n    class C:\n        x = a\n    return C\n", (), ("a",)),
    ("def f(a):\n    class C:\n        def m(self): return a\n    return C\n", ("__classdict__",), ("a",)),
    ("def f(a, b):\n    class C:\n        a = a\n        def m(self): return b\n    return C\n", ("__classdict__",), ("b",)),
    ("def f(a):\n    class C(a): pass\n    return C\n", (), ()),
    ("def f(a):\n    class C(metaclass=a): pass\n    return C\n", (), ()),
    ("def f():\n    a = 1\n    class C:\n        nonlocal a\n        a = 2\n    return C\n", (), ("a",)),
    ("def f(z, a):\n    class C:\n        def m(self): return __class__, z, a\n    return C\n", ("__class__", "__classdict__"), ("a", "z")),
]
for source, cells, free in free_cases:
    ns = {"a": "global"}
    bodies(source, ns)
    ns["f"](*[type] * ns["f"].__code__.co_argcount)
    code = captured[-1].__code__
    assert_eq((code.co_cellvars, code.co_freevars), (cells, free), source)

# The namespace holds __classdictcell__, then __classcell__, after the body's names.
seen = []
class Recording(type):
    @classmethod
    def __prepare__(meta, name, bases): return {}
    def __new__(meta, name, bases, ns):
        seen.append(list(ns))
        cell = ns.get("__classdictcell__")
        seen.append(cell is not None and type(cell) is CellType and cell.cell_contents is ns)
        cls = super().__new__(meta, name, bases, ns)
        seen.append(cell is not None and cell.cell_contents is not ns and type(cell.cell_contents) is dict)
        seen.append("__classdictcell__" in ns)
        return cls
class E(metaclass=Recording):
    "doc"
    def g(self): return __class__
assert_eq(seen, [["__module__", "__qualname__", "__firstlineno__", "__doc__", "g", "__static_attributes__", "__classdictcell__", "__classcell__"],
                 True, True, True])
assert_true("__classdictcell__" not in E.__dict__ and "__classcell__" not in E.__dict__)
del seen[:]
class F(metaclass=Recording):
    x = 1
assert_eq(seen, [["__module__", "__qualname__", "__firstlineno__", "x", "__static_attributes__"], False, False, False])

# Annotation scopes read the class's dictionary after the class is made.
class G:
    x: T
    T = int
    def m[U](self) -> T: pass
    type Alias = T
G.T = str
assert_eq((G.__annotations__, G.m.__annotations__, G.Alias.__value__), ({"x": str}, {"return": str}, str))
class H:
    y: Missing
H.Missing = bytes
assert_eq(H.__annotations__, {"y": bytes})

# type.__new__ checks the cell and fills it with the class dictionary.
for key in ("__classdictcell__", "__classcell__"):
    for bad in (1, None):
        e = assert_raises(TypeError, type, "X", (), {key: bad})
        assert_eq(str(e), "%s must be a nonlocal cell, not %r" % (key, type(bad)))
holder = CellType("before")
K = type("K", (), {"__classdictcell__": holder, "v": 1})
assert_eq((type(holder.cell_contents), holder.cell_contents["v"], "__classdictcell__" in K.__dict__), (dict, 1, False))
K.w = 2
assert_eq(holder.cell_contents["w"], 2)

# Calling a function of class body code runs the body with the globals as its namespace.
body, plain = bodies("class C:\n    'doc'\n    x = 1\n    def m(self): return __class__\nclass D:\n    y = 2\n    def n(self): self.q = 1\n")
g = {"__name__": "gm"}
f = FunctionType(body, g)
assert_eq((f.__name__, f.__qualname__, f.__defaults__, f.__closure__), ("C", "C", None, None))
result = f()
assert_eq(type(result), CellType)
assert_raises(ValueError, lambda: result.cell_contents)
assert_eq(sorted(k for k in g if k != "__builtins__"),
          ["__classcell__", "__classdictcell__", "__doc__", "__firstlineno__", "__module__", "__name__", "__qualname__", "__static_attributes__", "m", "x"])
assert_eq((g["x"], g["__qualname__"], g["__module__"], g["__doc__"], g["__static_attributes__"]), (1, "C", "gm", "doc", ()))
assert_true(g["__classcell__"] is result and g["__classdictcell__"].cell_contents is g)
assert_eq(str(assert_raises(TypeError, f, 1)), "C() takes 0 positional arguments but 1 was given")
assert_eq(str(assert_raises(TypeError, f, 1, 2)), "C() takes 0 positional arguments but 2 were given")
assert_eq(str(assert_raises(TypeError, lambda: f(a=1))), "C() got an unexpected keyword argument 'a'")

# Body code assigned to a function's __code__; the body without __class__ returns None.
target = FunctionType((lambda: None).__code__, {"__name__": "t"})
target.__code__ = plain
assert_eq(target(), None)
assert_eq((target.__globals__["y"], target.__globals__["__qualname__"], target.__globals__["__static_attributes__"]), (2, "D", ("q",)))

# Free variables of the body are the function's closure cells.
ns = {}
bodies("def f(a):\n    class C:\n        x = a\n        def get(self): return a\n    return C\n", ns)
ns["f"](0)
body = captured[-1].__code__
g2 = {"__name__": "free"}
cell = CellType(41)
f2 = FunctionType(body, g2, None, None, (cell,))
f2()
cell.cell_contents = 42
assert_eq((g2["x"], g2["get"](None)), (41, 42))
assert_eq(str(assert_raises(TypeError, FunctionType, body, g2)), "arg 5 (closure) must be tuple")

# A body with a __classdict__ cell still has its descriptors named and its
# base's __init_subclass__ called, and its slots laid out.
names = []
class Named:
    def __set_name__(self, owner, name): names.append(name)
class Base:
    def __init_subclass__(cls, **kw): names.append(("init", cls.__name__, kw))
class WithMethods(Base, flag=1):
    __slots__ = ("a",)
    first = Named()
    def method(self): return __class__
    second = Named()
    @property
    def prop(self): return 1
    @prop.setter
    def renamed(self, value): pass
assert_eq(names, ["first", "second", ("init", "WithMethods", {"flag": 1})])
assert_eq((WithMethods.prop.__name__, WithMethods.renamed.__name__, WithMethods().method()), ("prop", "renamed", WithMethods))
class SameSlots(Base):
    __slots__ = ("a",)
    def method(self): pass
class OtherLayout:
    __slots__ = ("a",)
    def method(self): pass
instance = WithMethods()
instance.__class__ = SameSlots
assert_eq(type(instance), SameSlots)
e = assert_raises(TypeError, setattr, instance, "__class__", OtherLayout)
assert_eq(str(e), "__class__ assignment: 'OtherLayout' object layout differs from 'SameSlots'")
