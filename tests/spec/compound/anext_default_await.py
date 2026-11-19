# spec: PLS-315 19.3.4, 15.3.2
# description: an await of anext() with a default of an async iterator
# whose __anext__ is a coroutine runs that coroutine in turn: what it
# returns is the await's value, its StopAsyncIteration gives the default,
# another exception propagates; while it waits at a yielding await, the
# awaiting coroutine's cr_await is the anext awaitable, a send reaches the
# yield, a throw raises there, and a close throws GeneratorExit in.
from harness import *

class Pause:
    def __await__(self):
        got = yield "paused"
        return got

class Items:
    def __init__(self, *steps): self.steps = list(steps)
    def __aiter__(self): return self
    async def __anext__(self):
        step = self.steps.pop(0)
        if step == "end": raise StopAsyncIteration
        if step == "fail": raise ValueError("failed")
        if step == "pause":
            try: return await Pause()
            except KeyError as e: return ("caught", e.args)
            except GeneratorExit:
                log.append("exit")
                raise
        if step == "stop":
            try: await Pause()
            except KeyError: raise StopAsyncIteration
        return step

log = []
def drive(aw, sends=()):
    sends = list(sends)
    try:
        got = aw.send(None)
        while True:
            log.append(got)
            got = aw.send(sends.pop(0))
    except StopIteration as e:
        return e.value

async def plain():
    it = Items(1, "end", "fail")
    out = [await anext(it, "d"), await anext(it, "d")]
    try: await anext(it, "d")
    except ValueError as e: out.append(e.args)
    return out
assert_eq(drive(plain()), [1, "d", ("failed",)])

async def paused():
    return await anext(Items("pause"), "d")
log = []
assert_eq(drive(paused(), ["sent"]), "sent")
assert_eq(log, ["paused"])

async def nested():
    it = Items("pause", "end")
    return [await anext(it, "d"), await anext(it, "d")]
log = []
assert_eq(drive(nested(), [5]), [5, "d"])

# cr_await, then a throw caught inside
co = paused()
assert_eq(co.send(None), "paused")
assert_eq(type(co.cr_await).__name__, "anext_awaitable")
try: co.throw(KeyError("k"))
except StopIteration as e: assert_eq(e.value, ("caught", ("k",)))
else: fail("no exception")
assert_is(co.cr_await, None)

# a throw ending the __anext__ coroutine with StopAsyncIteration gives the default
async def stopped():
    return await anext(Items("stop"), "d")
co = stopped()
assert_eq(co.send(None), "paused")
try: co.throw(KeyError)
except StopIteration as e: assert_eq(e.value, "d")
else: fail("no exception")

# a throw the coroutine does not catch propagates
co = paused()
co.send(None)
try: co.throw(IndexError("i"))
except IndexError as e: assert_eq(e.args, ("i",))
else: fail("no exception")

# a close throws GeneratorExit into the __anext__ coroutine
log = []
co = paused()
co.send(None)
assert_is(co.close(), None)
assert_eq(log, ["exit"])
assert_is(co.cr_await, None)

# a second await of the same awaitable after the coroutine finished
async def twice():
    aw = anext(Items(1), "d")
    first = await aw
    try: await aw
    except RuntimeError as e: return first, str(e)
assert_eq(drive(twice()), (1, "cannot reuse already awaited coroutine"))

# inside an async generator
async def agen():
    it = Items("pause", "end")
    yield await anext(it, "d")
    yield await anext(it, "d")
async def collect():
    return [x async for x in agen()]
log = []
assert_eq(drive(collect(), [7]), [7, "d"])
