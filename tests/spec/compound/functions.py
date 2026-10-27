# spec: PLS-315 16.1, 7.4.3
# description: Parameters, defaults, decorators, annotations, function attributes, and call-time binding errors.
from harness import *

def f(a, b=2, /, c=3, *args, d, e=5, **kw):
    return a, b, c, args, d, e, kw
assert_eq(f(1, d=4), (1, 2, 3, (), 4, 5, {}))
assert_eq(f(1, 9, 8, 7, 6, d=4, z=0), (1, 9, 8, (7, 6), 4, 5, {"z": 0}))
assert_eq(f(1, c=0, d=1, a=2), (1, 2, 0, (), 1, 5, {"a": 2}))
e = assert_raises(TypeError, f, 1)
assert_eq(str(e), "f() missing 1 required keyword-only argument: 'd'")
e = assert_raises(TypeError, f)
assert_eq(str(e), "f() missing 1 required positional argument: 'a'")
def g(a, b): pass
e = assert_raises(TypeError, g, 1, 2, 3)
assert_eq(str(e), "g() takes 2 positional arguments but 3 were given")
e = assert_raises(TypeError, g, 1, b=2, c=3)
assert_eq(str(e), "g() got an unexpected keyword argument 'c'")
e = assert_raises(TypeError, g, 1, a=2)
assert_eq(str(e), "g() got multiple values for argument 'a'")
def p(a, /): pass
e = assert_raises(TypeError, p, a=1)
assert_eq(str(e), "p() got some positional-only arguments passed as keyword arguments: 'a'")
def k(*, a): pass
e = assert_raises(TypeError, k, 1)
assert_eq(str(e), "k() takes 0 positional arguments but 1 was given")
e = assert_raises(TypeError, g)
assert_eq(str(e), "g() missing 2 required positional arguments: 'a' and 'b'")

# Defaults are evaluated once, at definition time, left to right.
log = []
def default(x):
    log.append(x)
    return x
def h(a=default(1), *, b=default(2)): return a, b
assert_eq(log, [1, 2])
def accumulate(x, into=[]):
    into.append(x)
    return into
accumulate(1)
assert_eq(accumulate(2), [1, 2])
assert_eq(h.__defaults__, (1,))
assert_eq(h.__kwdefaults__, {"b": 2})
h.__defaults__ = (10,)
assert_eq(h(), (10, 2))

# Syntax rules for parameters.
assert_syntax_error("def f(a=1, b): pass")
assert_syntax_error("def f(a, a): pass")
assert_syntax_error("def f(*, **kw): pass")
assert_syntax_error("def f(*): pass")
assert_syntax_error("def f(**kw, a): pass")
assert_syntax_error("def f(/, a): pass")
assert_syntax_error("def f(a, /, /): pass")
assert_syntax_error("def f(*a, /): pass")
assert_syntax_error("def f(*a, *b): pass")
assert_syntax_error("lambda a, a: 0")
assert_compiles("def f(a, /, b, *, c): pass")
assert_compiles("def f(a=1, /, b=2, *, c, d=4): pass")
assert_compiles("lambda a, /, b=1, *c, d, **e: 0")

# Decorators apply bottom-up after the function is created; any expression works (PEP 614).
order = []
def deco(name):
    def wrap(func):
        order.append(name)
        func.tags = getattr(func, "tags", []) + [name]
        return func
    return wrap
decorators = [deco("list")]
@deco("outer")
@decorators[0]
@(lambda func: deco("lambda")(func))
def decorated(): pass
assert_eq(order, ["lambda", "list", "outer"])
assert_eq(decorated.tags, ["lambda", "list", "outer"])
@deco("cls")
class Decorated: pass
assert_eq(Decorated.tags, ["cls"])

# Function attributes.
def documented(x: int, *args: str, y: "fwd" = 1, **kw: float) -> bool:
    "Docstring."
    return True
assert_eq(documented.__name__, "documented")
assert_eq(documented.__qualname__, "documented")
assert_eq(documented.__doc__, "Docstring.")
assert_eq(documented.__module__, "__main__")
assert_eq(documented.__annotations__, {"x": int, "args": str, "y": "fwd", "kw": float, "return": bool})
assert_eq(documented.__annotate__(1)["return"], bool)
assert_eq(documented.__annotate__(2)["x"], int)
assert_raises(NotImplementedError, documented.__annotate__, 3)
assert_eq(documented.__code__.co_argcount, 1)
assert_eq(documented.__code__.co_kwonlyargcount, 1)
assert_eq(documented.__code__.co_varnames[:4], ("x", "y", "args", "kw"))
assert_is(documented.__globals__, globals())
assert_eq(documented.__dict__, {})
documented.custom = 1
assert_eq(documented.__dict__, {"custom": 1})
assert_is(documented.__closure__, None)
assert_eq(documented.__type_params__, ())
def nodoc(): pass
assert_is(nodoc.__doc__, None)
def notdoc():
    x = 1
    "not a docstring"
assert_is(notdoc.__doc__, None)
assert_eq((lambda: 0).__name__, "<lambda>")
class Outer:
    def method(self):
        def inner(): pass
        return inner
assert_eq(Outer.method.__qualname__, "Outer.method")
assert_eq(Outer().method().__qualname__, "Outer.method.<locals>.inner")
assert_raises(TypeError, setattr, documented, "__name__", 1)
assert_raises(TypeError, setattr, documented, "__defaults__", 1)
# A function with no return statement returns None.
def none(): pass
assert_is(none(), None)
# Recursion and late binding of globals.
def fact(n): return 1 if n <= 1 else n * fact(n - 1)
assert_eq(fact(20), 2432902008176640000)
def late(): return later_name
later_name = "late"
assert_eq(late(), "late")
