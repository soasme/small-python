# spec: PLS-315 7.4.3
# description: Keyword arguments and defaults bind by name, read the current
# __defaults__ and __kwdefaults__, and reject every unmatched or repeated name.
from harness import *

def f(a, b=1, *, c=2, d): return (a, b, c, d)
assert_eq(f(1, d=4), (1, 1, 2, 4))
assert_eq(f(1, 2, d=4, c=3), (1, 2, 3, 4))
assert_eq(f(d=0, a=9), (9, 1, 2, 0))
assert_eq(f(**{"a": 5, "d": 6}), (5, 1, 2, 6))

# A keyword built at run time matches a parameter of equal spelling.
name = "".join(["d"])
assert_eq(f(1, **{name: 7}), (1, 1, 2, 7))

def g(): return 0
e = assert_raises(TypeError, lambda: g(x=1))
assert_eq(str(e), "g() got an unexpected keyword argument 'x'")
e = assert_raises(TypeError, lambda: f(1, a=2, d=1))
assert_eq(str(e), "f() got multiple values for argument 'a'")
e = assert_raises(TypeError, lambda: f(1))
assert_eq(str(e), "f() missing 1 required keyword-only argument: 'd'")
e = assert_raises(TypeError, lambda: f(1, 2, 3, d=1))
assert_eq(str(e), "f() takes from 1 to 2 positional arguments but 3 positional arguments (and 1 keyword-only argument) were given")
e = assert_raises(TypeError, lambda: f(1, d=1, dd=2))
assert_eq(str(e), "f() got an unexpected keyword argument 'dd'. Did you mean 'd'?")

def p(a, /, b=5): return (a, b)
assert_eq(p(1, b=2), (1, 2))
e = assert_raises(TypeError, lambda: p(a=1))
assert_eq(str(e), "p() got some positional-only arguments passed as keyword arguments: 'a'")

# Defaults are read from the function at each call.
def h(a, b=[]): b.append(a); return b
assert_eq(h(1), [1])
assert_eq(h(2), [1, 2])
h.__defaults__ = ([10],)
assert_eq(h(a=3), [10, 3])
h.__defaults__ = None
e = assert_raises(TypeError, lambda: h(a=3))
assert_eq(str(e), "h() missing 1 required positional argument: 'b'")
f.__kwdefaults__ = {"c": 7, "d": 8}
assert_eq(f(1), (1, 1, 7, 8))
del f.__kwdefaults__
e = assert_raises(TypeError, lambda: f(1, d=0))
assert_eq(str(e), "f() missing 1 required keyword-only argument: 'c'")

# A failed binding leaves no state behind for the next call.
def k(x, y=2): return x + y
assert_raises(TypeError, lambda: k(z=1))
assert_eq(k(y=1, x=2), 3)
assert_eq(sum(k(i) for i in range(5)), 20)

# Recursive and closure-capturing functions bind keywords in each frame.
def depth(n, acc=0): return acc if n == 0 else depth(n=n - 1, acc=acc + n)
assert_eq(depth(n=50), 1275)
def outer(a, b=3):
    def inner(): return a * b
    return inner
assert_eq(outer(b=4, a=2)(), 8)

# A failed binding raises from a body that calls, whether the arguments are
# computed in place or by calls of their own.
def one(a): return len([a])
def none_given(): return one()
def two_operands(x): return one(x + 1, x)
def two_calls(x): return one(len([x]), x)
e = assert_raises(TypeError, none_given)
assert_eq(str(e), "one() missing 1 required positional argument: 'a'")
for call in (lambda: two_operands(1), lambda: two_calls(1)):
    e = assert_raises(TypeError, call)
    assert_eq(str(e), "one() takes 1 positional argument but 2 were given")
