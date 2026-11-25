# spec: PLS-315 16.3, 16.6.3, 16.7
# description: Lambdas and generator expressions inside annotation scopes
# (annotate functions, type alias values, type parameter bounds and
# defaults) are named where the scope's owner is; inside a type parameter's
# lazy value or a generic alias's value, under the definition's
# <generic parameters of name>.
from harness import *

class C:
    f: lambda: 3
    def m(self, a: lambda: 1) -> (lambda: 2): pass
    type T = lambda: 4
    def gm[U: (lambda: 5)](self): pass

assert_eq(C.__annotations__["f"].__qualname__, "C.<lambda>")
assert_eq([v.__qualname__ for v in C.m.__annotations__.values()], ["C.<lambda>", "C.<lambda>"])
assert_eq(C.T.__value__.__qualname__, "C.<lambda>")
assert_eq(C.gm.__type_params__[0].__bound__.__qualname__, "C.<generic parameters of gm>.<lambda>")

def g(a: lambda: 1): pass
assert_eq(g.__annotations__["a"].__qualname__, "<lambda>")

def outer():
    def g(a: lambda: (lambda: 1)): pass
    type T = lambda: 3
    class D:
        y: lambda: 4
    def gh[X: (lambda: 1)](): pass
    class GC[Y: (lambda: 2)]: pass
    return g, T, D, gh, GC

g2, T2, D2, gh, GC = outer()
assert_eq(g2.__annotations__["a"].__qualname__, "outer.<locals>.<lambda>")
assert_eq(g2.__annotations__["a"]().__qualname__, "outer.<locals>.<lambda>.<locals>.<lambda>")
assert_eq(T2.__value__.__qualname__, "outer.<locals>.<lambda>")
assert_eq(D2.__annotations__["y"].__qualname__, "outer.<locals>.D.<lambda>")
assert_eq(gh.__type_params__[0].__bound__.__qualname__, "outer.<locals>.<generic parameters of gh>.<lambda>")
assert_eq(GC.__type_params__[0].__bound__.__qualname__, "outer.<locals>.<generic parameters of GC>.<lambda>")

type A[W: (lambda: 1), *Ts = (lambda: 2)] = lambda: 3
assert_eq([A.__type_params__[0].__bound__.__qualname__, A.__type_params__[1].__default__.__qualname__, A.__value__.__qualname__],
          ["<generic parameters of A>.<lambda>"] * 3)

x: lambda: 9
assert_eq(__annotate__(1)["x"].__qualname__, "<lambda>")

class G[V]:
    z: lambda: 1
    w: (i for i in ())
assert_eq((G.__annotations__["z"].__qualname__, G.__annotations__["w"].__qualname__), ("G.<lambda>", "G.<genexpr>"))
