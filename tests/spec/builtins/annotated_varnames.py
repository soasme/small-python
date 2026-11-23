# spec: PLS-315 28.2, 8.4
# description: A function's name only annotated without a value is not in
# co_varnames until the body otherwise binds, reads or deletes it, and then
# takes that place; it is still a local of the function.
from harness import *


def only():
    x: int
    y: int = 1
    return y


assert_eq(only.__code__.co_varnames, ("y",))
assert_eq(only.__code__.co_nlocals, 1)


def later():
    x: int
    y = 1
    x = 2


assert_eq(later.__code__.co_varnames, ("y", "x"))


def twice():
    x: int
    x: str


assert_eq(twice.__code__.co_varnames, ())


def read():
    x: int
    return x


assert_eq(read.__code__.co_varnames, ("x",))
assert_raises(UnboundLocalError, read)


def deleted():
    x: int
    del x


assert_eq(deleted.__code__.co_varnames, ("x",))


def enclosing():
    x: int
    def inner():
        nonlocal x
        x = 1
    inner()
    return x


assert_eq(enclosing(), 1)
assert_eq(enclosing.__code__.co_varnames, ("inner",))
assert_eq(enclosing.__code__.co_cellvars, ("x",))


def snapshot():
    x: int
    return locals()


assert_eq(snapshot(), {})
assert_eq(snapshot.__code__.co_nlocals, 0)

assert_eq(assert_syntax_error("def f():\n    x: int\n    global x\n").msg, "annotated name 'x' can't be global")
assert_eq(assert_syntax_error("def f():\n    __debug__: int\n").msg, "cannot assign to __debug__")
