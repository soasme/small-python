# spec: PLS-315 19.3.25
# description: locals() at module and function scope.
from harness import *
a = 5
b = 6

loc = locals()

assert loc["a"] == 5
assert loc["b"] == 6


def f():
    c = 4
    a = 7

    loc = locals()

    assert loc["a"] == 4
    assert loc["c"] == 7
    assert not "b" in loc


# The snapshot follows co_varnames: positional and keyword-only parameters,
# *args, **kwargs, then the other locals, whatever order the call bound them in.
def order(a, *args, b, c=3, **kw):
    x = 1
    return list(locals())


assert order(1, b=2) == ["a", "b", "c", "args", "kw", "x"]
assert order(1, 2, z=4, b=2) == ["a", "b", "c", "args", "kw", "x"]
assert order.__code__.co_varnames == ("a", "b", "c", "args", "kw", "x")


def g(p, q=5):
    return list(locals())


assert g(q=2, p=1) == ["p", "q"]


# Cells that are not parameters follow the other locals in co_cellvars order
# (parameter cells first, then sorted), and free names come last.
def cells(y, x, *, w):
    d = 1
    c = 2
    def inner(): return x, y, w, c, d
    return list(locals())


assert cells(1, 2, w=3) == ["y", "x", "w", "inner", "c", "d"]
assert cells.__code__.co_cellvars == ("y", "x", "w", "c", "d")


def outer():
    m = 1
    def middle():
        b = 2
        a = 1
        def innermost(): return a, b, m
        return list(locals()), middle.__code__.co_freevars
    return middle()


assert outer() == (["innermost", "a", "b", "m", "middle"], ("m", "middle"))
