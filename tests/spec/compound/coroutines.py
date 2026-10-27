# spec: PLS-315 27.3, 27.4, 13.4
# description: Coroutine objects, awaitables, the coroutine wrapper, awaiting once, and iterable coroutines.
from harness import *

def drive(coroutine):
    yielded = []
    try:
        value = None
        while True:
            yielded.append(coroutine.send(value))
            value = len(yielded)
    except StopIteration as stop:
        return yielded, stop.value

started = []
async def body():
    started.append(1)
    return "result"
c = body()
assert_eq(started, [])
assert_eq(c.cr_running, False)
assert_eq(c.cr_suspended, False)
assert_is(c.cr_await, None)
assert_eq(c.cr_code.co_name, "body")
assert_true(c.cr_frame is not None)
assert_is(c.cr_origin, None)
assert_true(repr(c).startswith("<coroutine object body at "))
e = assert_raises(TypeError, iter, c)
assert_eq(str(e), "'coroutine' object is not iterable")
assert_false(hasattr(c, "__next__"))
assert_eq(drive(c), ([], "result"))
assert_eq(started, [1])
assert_is(c.cr_frame, None)

# Awaitables: the yielded values pass out; StopIteration's value is the result.
class Ready:
    def __await__(self):
        value = yield "suspend"
        return value * 10
async def uses():
    first = await Ready()
    second = await Ready()
    return first + second
assert_eq(drive(uses()), (["suspend", "suspend"], 10 + 20))
async def waiting():
    await Ready()
w = waiting()
w.send(None)
assert_true(w.cr_suspended)
assert_eq(type(w.cr_await).__name__, "generator")
w.close()
assert_is(w.cr_frame, None)

# send, throw and close as for generators.
async def catches():
    try:
        await Ready()
    except KeyError:
        return "caught"
t = catches()
t.send(None)
assert_eq(assert_raises(StopIteration, t.throw, KeyError()).value, "caught")
e = assert_raises(TypeError, catches().send, 1)
assert_eq(str(e), "can't send non-None value to a just-started coroutine")

# __await__ returns a coroutine wrapper driving the coroutine.
co = body()
wrapper = co.__await__()
assert_eq(type(wrapper).__name__, "coroutine_wrapper")
assert_is(iter(wrapper), wrapper)
assert_eq(assert_raises(StopIteration, next, wrapper).value, "result")
wrapper.close()
r = uses()
rw = r.__await__()
assert_eq(next(rw), "suspend")
assert_eq(rw.send(2), "suspend")
assert_eq(assert_raises(StopIteration, rw.send, 3).value, 50)
rw2 = waiting().__await__()
next(rw2)
assert_raises(ZeroDivisionError, rw2.throw, ZeroDivisionError())

# Awaiting once.
done = body()
drive(done)
async def again():
    return await done
e = assert_raises(RuntimeError, drive, again())
assert_eq(str(e), "cannot reuse already awaited coroutine")
shared = waiting()
async def first():
    await shared
async def second():
    await shared
f = first()
f.send(None)
e = assert_raises(RuntimeError, second().send, None)
assert_eq(str(e), "coroutine is being awaited already")
f.close()

# An iterable coroutine: a generator whose code has flag 0x100.
def legacy():
    value = yield "legacy"
    return value
legacy.__code__ = legacy.__code__.replace(co_flags=legacy.__code__.co_flags | 0x100)
async def await_legacy():
    return await legacy()
assert_eq(drive(await_legacy()), (["legacy"], 1))
def delegating():
    return (yield from body())
delegating.__code__ = delegating.__code__.replace(co_flags=delegating.__code__.co_flags | 0x100)
assert_eq(drive(delegating()), ([], "result"))
def plain():
    yield from body()
assert_raises(TypeError, next, plain())
