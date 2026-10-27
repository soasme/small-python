# spec: PLS-315 7.1.4
# description: __mro__ and mro() of single and multiple inheritance.
from harness import *
class X:
    pass


class Y:
    pass


class A(X, Y):
    pass


assert (A, X, Y, object) == A.__mro__


class B(X, Y):
    pass


assert (B, X, Y, object) == B.__mro__


class C(A, B):
    pass


assert (C, A, B, X, Y, object) == C.__mro__

assert type.__mro__ == (type, object)

# A failed merge names the distinct heads of the lists left to merge.
class P: pass
class Q(P): pass
assert_eq(str(assert_raises(TypeError, type, "R", (P, Q), {})),
          "Cannot create a consistent method resolution order (MRO) for bases P, Q")
class XY(X, Y): pass
class YX(Y, X): pass
assert_eq(str(assert_raises(TypeError, type, "Z", (XY, YX), {})),
          "Cannot create a consistent method resolution order (MRO) for bases X, Y")
