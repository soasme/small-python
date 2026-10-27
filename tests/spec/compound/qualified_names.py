# spec: PLS-315 16.3
# description: __qualname__ of functions, classes, lambdas and generator expressions.
from harness import *

def top(): pass
class C:
    def method(self): pass
    class Inner:
        def deep(self): pass
    lam = lambda: None
def outer():
    def inner(): pass
    class Local:
        def m(self): pass
    return inner, Local
inner, Local = outer()
assert_eq(top.__qualname__, "top")
assert_eq(C.__qualname__, "C")
assert_eq(C.method.__qualname__, "C.method")
assert_eq(C.Inner.__qualname__, "C.Inner")
assert_eq(C.Inner.deep.__qualname__, "C.Inner.deep")
assert_eq(C.lam.__qualname__, "C.<lambda>")
assert_eq(inner.__qualname__, "outer.<locals>.inner")
assert_eq(Local.__qualname__, "outer.<locals>.Local")
assert_eq(Local.m.__qualname__, "outer.<locals>.Local.m")
assert_eq(top.__name__, "top")
assert_eq(Local.m.__name__, "m")
assert_eq((lambda: None).__qualname__, "<lambda>")
genexp = (x for x in [])
assert_eq(genexp.__name__, "<genexpr>")
assert_eq(genexp.__qualname__, "<genexpr>")
def make_genexp():
    return (x for x in [])
assert_eq(make_genexp().__qualname__, "make_genexp.<locals>.<genexpr>")
def gen(): yield
assert_eq(gen().__qualname__, "gen")
assert_eq(C().method.__qualname__, "C.method")

# A global declaration gives a nested definition a top-level qualified name.
ns = run("def f():\n    global g\n    def g(): pass\n    class K:\n        global H\n        class H: pass\n    return K\n"
         "K = f()\n")
assert_eq(ns["g"].__qualname__, "g")
assert_eq(ns["H"].__qualname__, "H")
assert_eq(ns["K"].__qualname__, "f.<locals>.K")
ns = run("class A:\n    global B\n    class B:\n        def m(self): pass\n")
assert_eq(ns["B"].__qualname__, "B")
assert_eq(ns["B"].m.__qualname__, "B.m")

# __qualname__ is writable on functions and classes, and must be a str.
def renamed(): pass
renamed.__qualname__ = "X.y"
assert_eq(renamed.__qualname__, "X.y")
assert_raises(TypeError, setattr, renamed, "__qualname__", 1)
class R: pass
R.__qualname__ = "Q"
assert_eq(R.__qualname__, "Q")
assert_eq(R.__name__, "R")
