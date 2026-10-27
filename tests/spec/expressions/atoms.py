# spec: reference/expressions.html#atoms
# description: Built-in constants, names, literals, parenthesized forms, and displays.
from harness import *

assert_is(type(None).__name__, "NoneType") if False else None
assert_eq(type(None).__name__, "NoneType")
assert_eq(type(...).__name__, "ellipsis")
assert_eq(type(NotImplemented).__name__, "NotImplementedType")
assert_is(..., Ellipsis)
assert_true(True is not False)
assert_syntax_error("None = 1")
assert_syntax_error("True = 1")
assert_syntax_error("__debug__ = 1")
assert_syntax_error("def f(__debug__): pass")
assert_true(__debug__ in (True, False))

# An unbound name raises NameError; unbound local raises UnboundLocalError.
assert_raises(NameError, lambda: undefined_name_xyz)
def f():
    x
    x = 1
assert_raises(UnboundLocalError, f)
assert_true(issubclass(UnboundLocalError, NameError))
e = assert_raises(NameError, lambda: undefined_name_xyz)
assert_eq(e.name, "undefined_name_xyz")

# Parenthesized forms: () is the empty tuple; a parenthesized expression is that expression.
assert_eq((), tuple())
assert_eq((1), 1)
assert_eq((1,), tuple([1]))
assert_eq(((1, 2)), (1, 2))
assert_eq(1,  ) if False else None
t = 1, 2
assert_eq(t, (1, 2))
assert_eq((yield_ := 3), 3)

# Each evaluation of a list/dict/set display creates a new object.
def make():
    return [], {}, set()
a, b = make(), make()
assert_true(a[0] is not b[0] and a[1] is not b[1])

# Literals and identity: immutable literal values with the same value may or may not be the same object,
# but a tuple display with equal items compares equal.
assert_eq((1, 2), (1, 2))
