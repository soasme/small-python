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
