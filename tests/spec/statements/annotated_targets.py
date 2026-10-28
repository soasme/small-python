# spec: PLS-315 14.4, 8.2, 7.2, 28.5, 13.2.6
# description: Which annotated targets bind a name, __call__ on the callable built-in types, and the yield-in-comprehension message.
from harness import *

# A simple name target is local even without a value; a parenthesized one
# is local only when it has a value.
def simple():
    x: int
    return x
assert_raises(UnboundLocalError, simple)
def bare():
    (no_such_global): int
    return no_such_global
e = assert_raises(NameError, bare)
assert_is(type(e), NameError)
def valued():
    (x): int = 1
    return x
assert_eq(valued(), 1)
outer = "global"
def reads_global():
    (outer): int
    return outer
assert_eq(reads_global(), "global")
assert_eq(reads_global.__code__.co_varnames, ())

# Functions, built-in functions and bound methods have __call__ through their type.
def add(a, b=1):
    return a + b
class C:
    def m(self, k=0):
        return k
for f in (add, len, [].append, C().m, add.__call__):
    assert_true("__call__" in dir(f), f)
assert_true("__call__" in type(add).__dict__)
assert_eq(add.__call__(1), 2)
assert_eq(add.__call__.__call__(1, b=5), 6)
assert_eq(type(add).__call__(add, 2), 3)
assert_eq(len.__call__("abc"), 3)
assert_eq(C().m.__call__(k=4), 4)
for f in (add, len, C().m):
    assert_eq(type(f.__call__).__name__, "method-wrapper")
    assert_is(f.__call__.__self__, f)
assert_raises(TypeError, add.__call__)

# yield and yield from inside a comprehension are worded alike.
for source, kind in (("[(yield x) for x in ()]", "list comprehension"),
                     ("[(yield from x) for x in ()]", "list comprehension"),
                     ("{(yield from x) for x in ()}", "set comprehension"),
                     ("{x: (yield from x) for x in ()}", "dict comprehension"),
                     ("((yield from x) for x in ())", "generator expression")):
    e = assert_raises(SyntaxError, compile, "def g(): " + source, "<s>", "exec")
    assert_eq(e.msg, "'yield' inside " + kind)
