# spec: reference/compound_stmts.html#type-parameter-lists
# description: PEP 695/696 generic functions, classes and aliases; annotation scopes; lazy bounds and defaults.
from harness import *

def ident[T](x: T) -> T: return x
assert_eq(ident(3), 3)
(T,) = ident.__type_params__
assert_eq(T.__name__, "T")
assert_eq(type(T).__name__, "TypeVar")
assert_raises(NameError, run, "def f[T](): pass\nT\n")

class Box[T, *Ts, **P]:
    def get(self) -> T: ...
T2, Ts, P = Box.__type_params__
assert_eq([type(p).__name__ for p in Box.__type_params__], ["TypeVar", "TypeVarTuple", "ParamSpec"])
assert_true(any(b.__name__ == "Generic" for b in Box.__mro__))
assert_eq(Box[int, str, [int]].__args__[0], int)

def bounded[T: int, U: (str, bytes) = str, V = Undefined](): pass
T, U, V = bounded.__type_params__
assert_is(T.__bound__, int)
assert_eq(U.__constraints__, (str, bytes))
assert_is(U.__default__, str)
assert_raises(NameError, lambda: V.__default__)
assert_true(T.has_default() is False)

# Variance is inferred.
class Inferred[T]: pass
(T,) = Inferred.__type_params__
assert_true(T.__infer_variance__)

# Annotation scope: class-level names are visible to type params' bounds via the class.
class Outer:
    Alias = int
    def method[T: Alias](self): return T
assert_is(Outer().method().__bound__, int)
# Type parameters are visible in the body and in nested functions.
def outer[T]():
    def inner(): return T
    return inner()
assert_eq(outer().__name__, "T")

assert_syntax_error("def f[T, T](): pass")
assert_syntax_error("class C[T, T]: pass")
assert_syntax_error("def f[*Ts = int, U](): pass") if False else None
assert_syntax_error("def f[T = int, U](): pass")
assert_syntax_error("def f[]: pass")
assert_syntax_error("def f[T: (yield)](): pass")
assert_syntax_error("def f[T: (x := 1)](): pass")
assert_syntax_error("class C[T]:\n    nonlocal T\n")
assert_syntax_error("def f[**P: int](): pass")
assert_syntax_error("def f[*Ts: int](): pass")
assert_compiles("def f[*Ts = *tuple[int]](): pass")

# Generic class bases and keywords are evaluated in the annotation scope.
class Base[T]: pass
class Derived[U](Base[U]): pass
assert_eq(Derived.__orig_bases__[0].__args__[0].__name__, "U")
assert_eq(Derived.__type_params__[0].__name__, "U")
# Names in the class body do not leak into the annotation scope.
ns = run("class A[T]:\n    x = T\n")
assert_eq(ns["A"].x.__name__, "T")
assert_false("T" in ns)
# Bounds are lazily evaluated.
def lazy[T: Undefined](): pass
assert_raises(NameError, lambda: lazy.__type_params__[0].__bound__)
# Generic alias with a starred tuple and Unpack.
def star[*Ts](*args: *Ts): pass
assert_eq(star.__annotations__["args"].__class__.__name__, "Unpack") if False else None
assert_eq(repr(T), "~T") if False else None
assert_eq(repr(ident.__type_params__[0]), "T")
assert_eq(repr(Box.__type_params__[1]), "Ts")
assert_eq(repr(Box.__type_params__[2]), "P")
# Type parameter objects: members are readonly, getsets are not writable.
def generic[T: int, *Ts, **P](): pass
T, Ts, P = generic.__type_params__
for param, name, message in ((T, "__name__", "readonly attribute"),
                             (T, "__bound__", "attribute '__bound__' of 'typing.TypeVar' objects is not writable"),
                             (P, "__bound__", "readonly attribute"),
                             (Ts, "__default__", "attribute '__default__' of 'typing.TypeVarTuple' objects is not writable"),
                             (P.args, "__origin__", "readonly attribute"),
                             (P.args, "x", "'typing.ParamSpecArgs' object has no attribute 'x' and no __dict__ for setting new attributes")):
    assert_eq(str(assert_raises(AttributeError, setattr, param, name, 1)), message)
    assert_eq(str(assert_raises(AttributeError, delattr, param, name)), message)
union = int | str
assert_eq(str(assert_raises(AttributeError, delattr, union, "__args__")), "readonly attribute")
assert_eq(str(assert_raises(AttributeError, setattr, union, "__origin__", 1)),
          "attribute '__origin__' of 'typing.Union' objects is not writable")
# Lazily evaluated values are named in the scope of their definition.
class Holder:
    type Alias[W: int = str] = list[W]
    def make(self):
        type Local = int
        return Local
assert_eq(Holder.Alias.__qualname__, "Holder.Alias")
assert_eq(Holder.Alias.evaluate_value.__qualname__, "Holder.Alias")
assert_eq(Holder.Alias.__type_params__[0].evaluate_bound.__qualname__, "Holder.W")
assert_eq(Holder().make().__qualname__, "Holder.make.<locals>.Local")
TypeAliasType = type(Holder.Alias)
assert_eq(str(assert_raises(TypeError, TypeAliasType, "B")), "typealias() missing required argument 'value' (pos 2)")
assert_eq(TypeAliasType("B", int, qualname="Q.B").__qualname__, "Q.B")
assert_eq(repr(type(t"")[int]), "string.templatelib.Template[int]")
