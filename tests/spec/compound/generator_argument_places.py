# spec: PLS-315 13.2.6, 16.4
# description: a generator expression that is the sole argument of a call
# runs in its own scope wherever the call is: in a module, a function, a
# class body, a function's class body and a method, its first iterable
# evaluated where the call is and its element in its own scope.
from harness import *

def f(*a, **k): return a, k

y = [1, 2]
assert_eq(list(b * 2 for b in y), [2, 4])

class C:
    y = [3, 4]
    v = list(b for b in y)
    w = sorted(b for b in [2, 1] if b)
    s = sum(b * 2 for b in y)
    t = f(b for b in y)[0][0].__qualname__
    u = list(c for b in y for c in [b, -b])
    z = list((b for b in y))
    n = dict(a=1)
assert_eq((C.v, C.w, C.s, C.t, C.u, C.z, C.n), ([3, 4], [1, 2], 14, "C.<genexpr>", [3, -3, 4, -4], [3, 4], {"a": 1}))

def outer():
    q = [5]
    class D:
        v = list(b + q[0] for b in q)
        def m(self, d=list(b for b in q)): return d, list(b for b in d)
    return D.v, D().m()
assert_eq(outer(), ([10], ([5], [5])))

# The element is not in the class's scope; the first iterable is.
class E:
    x = 1
    k = [7]
    try: v = list(x for b in [1])
    except NameError as e: v = str(e)
    w = list(b for b in k)
assert_eq((E.v, E.w), ("name 'x' is not defined", [7]))

# A first argument that never closes ends the search for its for.
for source in ["f(x(", "f(x[", "f(x, (y", "f(x for x in (y"]:
    assert_eq(assert_syntax_error(source).msg[-16:], "was never closed", source)

# A starred element emits into its generator's own program too.
class S:
    k = [[1, 2], [3]]
    v = list(*x for x in k)
    w = sorted(*x for x in k for _ in (0, 1))
assert_eq((S.v, S.w), ([1, 2, 3], [1, 1, 2, 2, 3, 3]))
