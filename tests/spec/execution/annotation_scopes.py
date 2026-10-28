# spec: PLS-315 8.7, 13.16.3, 15.3.2
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
