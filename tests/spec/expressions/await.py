# spec: PLS-315 13.4, 7.7.5
# description: await is allowed only in async functions; it delegates to the awaitable's iterator.
from harness import *

assert_eq(assert_syntax_error("await x\n").msg, "'await' outside function")
assert_eq(assert_syntax_error("def f():\n    await x\n").msg, "'await' outside async function")
# An await in a comprehension makes it asynchronous (13.2.6).
assert_eq(assert_syntax_error("def f():\n    [await x for x in y]\n").msg,
          "asynchronous comprehension outside of an asynchronous function")
assert_compiles("async def f():\n    await x\n    [await y for y in z]\n")

def drive(coroutine):
    """Run a coroutine to completion, recording what it yields."""
    yielded = []
    try:
        value = None
        while True:
            yielded.append(coroutine.send(value))
            value = len(yielded)
    except StopIteration as stop:
        return yielded, stop.value

class Awaitable:
    def __await__(self):
        got = yield "first"
        got2 = yield "second"
        return ("done", got, got2)

async def use():
    return await Awaitable()
assert_eq(drive(use()), (["first", "second"], ("done", 1, 2)))

# Awaiting a coroutine runs it in the caller.
async def inner():
    return 42
async def outer():
    return await inner() + 1
assert_eq(drive(outer()), ([], 43))

# Exceptions propagate through await.
async def raises():
    raise KeyError("k")
async def catcher():
    try:
        await raises()
    except KeyError as e:
        return e.args
assert_eq(drive(catcher()), ([], ("k",)))

# The operand is evaluated before GetAwaitable checks it.
order = []
def operand():
    order.append("operand")
    return 1
async def bad():
    await operand()
e = assert_raises(TypeError, drive, bad())
assert_eq(str(e), "'int' object can't be awaited")
assert_eq(order, ["operand"])

# __await__ must return an iterator.
class NotIter:
    def __await__(self):
        return 1
async def bad_iter():
    await NotIter()
e = assert_raises(TypeError, drive, bad_iter())
assert_eq(str(e), f"{fqname(NotIter)}.__await__() must return an iterator, not int")
class ReturnsCoroutine:
    def __await__(self):
        return awaited
async def await_coroutine():
    await ReturnsCoroutine()
awaited = inner()
e = assert_raises(TypeError, drive, await_coroutine())
assert_eq(str(e), f"{fqname(ReturnsCoroutine)}.__await__() must return an iterator, not coroutine")
drive(awaited)

# A bare generator is not awaitable; a coroutine cannot be awaited twice.
def gen():
    yield
async def await_gen():
    await gen()
assert_raises(TypeError, drive, await_gen())
coroutine = inner()
async def twice():
    await coroutine
    await coroutine
e = assert_raises(RuntimeError, drive, twice())
assert_eq(str(e), "cannot reuse already awaited coroutine")
