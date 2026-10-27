# spec: PLS-315 28.1, 16.2
# description: The function type and its constructor.
from harness import *

FunctionType = type(lambda: None)
assert_eq(FunctionType.__name__, "function")
def template(a, b=2, *, c=3):
    return (a, b, c, scale)
scale = 10
g = {"__name__": "made", "scale": 5}
f = FunctionType(template.__code__, g)
assert_eq(f.__name__, "template")
assert_eq(f.__qualname__, "template")
assert_eq(f.__module__, "made")
assert_is(f.__globals__, g)
assert_raises(TypeError, f)
assert_eq(f(1, 2, c=3), (1, 2, 3, 5))
f2 = FunctionType(template.__code__, g, "renamed", (7,), None, {"c": 9})
assert_eq(f2.__name__, "renamed")
assert_eq(f2(1), (1, 7, 9, 5))
assert_eq(FunctionType(template.__code__, {"scale": 0}).__module__, None)

def outer():
    x = 1
    def inner():
        return x
    return inner
closed = outer()
cell = closed.__closure__[0]
rebuilt = FunctionType(closed.__code__, {}, None, None, (type(cell)(42),))
assert_eq(rebuilt(), 42)

def error(exc, *args):
    return str(assert_raises(exc, FunctionType, *args))
assert_eq(error(TypeError, 1, {}), "function() argument 'code' must be code, not int")
assert_eq(error(TypeError, template.__code__, []), "function() argument 'globals' must be dict, not list")
assert_eq(error(TypeError, template.__code__, {}, 1), "arg 3 (name) must be None or string")
assert_eq(error(TypeError, template.__code__, {}, None, [1]), "arg 4 (defaults) must be None or tuple")
assert_eq(error(TypeError, closed.__code__, {}, None, None, [cell]), "arg 5 (closure) must be None or tuple")
assert_eq(error(TypeError, closed.__code__, {}, None, None, (1,)), "arg 5 (closure) expected cell, found int")
assert_eq(error(ValueError, closed.__code__, {}, None, None, ()), "inner requires closure of length 1, not 0")
assert_eq(error(ValueError, template.__code__, {}, None, None, (cell,)), "template requires closure of length 0, not 1")
