# spec: PLS-315 8.7, 13.16.3, 15.3.2, 16.6.4
# description: Annotation scopes reject their own yield, await and named expressions; coroutines and __anext__ awaitables fail as specified.
from harness import *


def check(source, message, offset, end_offset):
    error = assert_syntax_error(source)
    assert_eq((error.msg, error.offset, error.end_offset), (message, offset, end_offset), repr(source))


# 8.7: each annotation scope names itself; the error spans the expression.
check("type T = await x", "await expression cannot be used within a type alias", 10, 17)
check("def f[T: (yield)](): pass", "yield expression cannot be used within a TypeVar bound", 11, 16)
check("def f[T: ((y := 1), int)](): pass", "named expression cannot be used within a TypeVar constraint", 12, 18)
check("def f[T = await x](): pass", "await expression cannot be used within a TypeVar default", 11, 18)
check("def f[*T = await x](): pass", "await expression cannot be used within a TypeVarTuple default", 12, 19)
check("def f[**T = await x](): pass", "await expression cannot be used within a ParamSpec default", 13, 20)
check("class C[T](await x): pass", "await expression cannot be used within the definition of a generic", 12, 19)
check("def f(x: (yield from x)): pass", "yield expression cannot be used within an annotation", 11, 23)
check("x: (y := 1)", "named expression cannot be used within an annotation", 5, 11)
# A comprehension is a scope of its own; its first iterable is not.
check("type T = [await x for x in y]", "asynchronous comprehension outside of an asynchronous function", 10, 30)
check("type T = [x for x in await y]", "await expression cannot be used within a type alias", 22, 29)
assert_compiles("def f[T: (await x for x in y)](): pass")
# Scope analysis runs only after the whole source parses.
check("type T = await x\nx y", "invalid syntax", 3, 4)

# Annotations that are never evaluated follow the same rule: in a function
# body, on a target that is not a simple name, and as strings (16.6.4).
future = "from __future__ import annotations\n"
def check2(source, message, offset, end_offset):
    error = assert_syntax_error(source)
    assert_eq((error.msg, error.lineno, error.offset, error.end_offset), (message, 2, offset, end_offset), repr(source))
check2("def g():\n    x: (yield) = 1", "yield expression cannot be used within an annotation", 9, 14)
check2("def g():\n    x: [y := 1] = 1", "named expression cannot be used within an annotation", 9, 15)
check2("def g():\n    (x): (yield) = 1", "yield expression cannot be used within an annotation", 11, 16)
check("x.y: (yield) = 1", "yield expression cannot be used within an annotation", 7, 12)
check2(future + "def f(x: (yield)): pass", "yield expression cannot be used within an annotation", 11, 16)
check2(future + "async def f(x: (await y)): pass", "await expression cannot be used within an annotation", 17, 24)
check2(future + "def f() -> (await x): pass", "await expression cannot be used within an annotation", 13, 20)
check2(future + "x: (y := 1) = 2", "named expression cannot be used within an annotation", 5, 11)
error = assert_syntax_error(future + "class C:\n    x: (yield)")
assert_eq((error.msg, error.lineno), ("yield expression cannot be used within an annotation", 3))
error = assert_syntax_error(future + "def f(x: (yield)): pass\nx y")
assert_eq((error.msg, error.lineno), ("invalid syntax", 3))
# A lambda or comprehension inside one is a scope of its own: in a function
# body it can capture a local, and as a string it keeps its spelling.
def captures():
    x = 1
    z: (lambda: x) = 3
    w: [x for _ in ()] = 3
assert_eq(captures.__code__.co_cellvars, ("x",))
namespace = run(future + """
def f(a: lambda: (yield), b: lambda: (yield 1), c: lambda: (yield from x), d: [(y := 1) for z in w],
      h: True, i: ..., j: x if y else z, k: {**a, "k": v}, l: f(*a, **b, k=1)) -> lambda: (z := 2): pass
""")
assert_eq(namespace["f"].__annotations__, {"a": "lambda: (yield)", "b": "lambda: (yield 1)", "c": "lambda: (yield from x)",
    "d": "[(y := 1) for z in w]", "h": "True", "i": "...", "j": "x if y else z", "k": "{**a, 'k': v}",
    "l": "f(*a, **b, k=1)", "return": "lambda: (z := 2)"})

# 13.16.3: only an iterable coroutine may delegate to a coroutine.
async def value():
    return 10


def plain():
    yield from coroutine


coroutine = value()
error = assert_raises(TypeError, list, plain())
assert_eq(str(error), "cannot 'yield from' a coroutine object in a non-coroutine generator")
iterable = plain.__code__.replace(co_flags=plain.__code__.co_flags | 0x100)
plain.__code__ = iterable
assert_raises(StopIteration, plain().send, None)
coroutine.close()


# 15.3.2: a failing GetAwaitable becomes the cause of the TypeError.
class Next:
    def __aiter__(self):
        return self

    def __anext__(self):
        return self

    def __await__(self):
        1 / 0


async def loop():
    async for _ in Next():
        pass


error = assert_raises(TypeError, loop().send, None)
assert_eq(str(error), "'async for' received an invalid object from __anext__: Next")
assert_type(error.__cause__, ZeroDivisionError)
assert_is(error.__context__, error.__cause__)
# A string annotation is analysed whole, in an annotation scope of its own:
# its lambdas and comprehensions follow their usual rules, and it captures
# nothing. No annotation scope is asynchronous.
for source, message in (("lambda: (await x)", "'await' outside async function"),
                        ("[(yield) for x in y]", "'yield' inside list comprehension"),
                        ("[x for x in (yield)]", "yield expression cannot be used within an annotation"),
                        ("lambda: [(x := 1) for x in y]", "assignment expression cannot rebind comprehension iteration variable 'x'"),
                        ("lambda x, x: 1", "duplicate parameter 'x' in function definition"),
                        ("[q async for q in r]", "asynchronous comprehension outside of an asynchronous function")):
    for head in ("def f():\n    a: ", "async def f():\n    a: ", "class C:\n    a: ", "a: "):
        error = assert_syntax_error(future + head + source)
        assert_eq(error.msg, message, head + source)
for source in ("async def f():\n    x: [q async for q in r]", "async def f(a: [q async for q in r]): pass",
               "async def f[T: [q async for q in r]](): pass"):
    assert_eq(assert_syntax_error(source).msg, "asynchronous comprehension outside of an asynchronous function", source)
assert_eq(run(future + "def outer():\n    y = 1\n    def f():\n        x: lambda: y\n    return f\n")["outer"].__code__.co_cellvars, ())
