# spec: PLS-315 16.3, 16.6, 16.7
# description: an annotate function is named __annotate__ and qualified by
# its owner, except a top-level generic function's, which is __annotate__
# alone; a nested or method generic keeps its owner's qualified name.
from harness import *
def g[T](a: T) -> T: pass
def h(a: int): pass
class C[T]:
    x: T
    def m[U](self, a: U): pass
def outer():
    def g[T](a: T): pass
    return g
assert_eq([f.__annotate__.__name__ for f in (g, h, C, C.m, outer())], ["__annotate__"] * 5)
assert_eq([f.__annotate__.__qualname__ for f in (g, h, C, C.m, outer())],
          ["__annotate__", "h.__annotate__", "C.__annotate__", "C.m.__annotate__", "outer.<locals>.g.__annotate__"])
assert_eq(g.__annotate__(1), {"a": g.__type_params__[0], "return": g.__type_params__[0]})
