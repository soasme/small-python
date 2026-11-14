# spec: PLS-315 13.4, 15.3.2, 27.5.1
# description: awaiting an async generator's asend() or __anext__(), and an
# async for over one, resume its body: what asend sends reaches its yield,
# its awaits pass their values through to the driver, a yield finishes the
# await with its value, and its end raises StopAsyncIteration or ends the
# loop; its errors propagate, an awaited one cannot be reused, one of a
# running generator raises, and a throw or close of the driver reaches the
# body at its await.
from harness import *

class Pause:
    def __init__(self, tag): self.tag = tag
    def __await__(self):
        got = yield self.tag
        return got

def drive(co, sends=()):
    sends, out = list(sends), []
    try:
        value = co.send(None)
        while True:
            out.append(value)
            value = co.send(sends.pop(0) if sends else None)
    except StopIteration as e:
        return out, e.value

log = []

async def counter(n):
    for i in range(n):
        log.append(("before", i))
        got = await Pause(i)
        sent = yield (i, got)
        log.append(("sent", sent))

async def sends():
    g = counter(3)
    a = await g.asend(None)
    b = await g.asend("x")
    c = await anext(g)
    try: await g.__anext__()
    except StopAsyncIteration: d = "end"
    return [a, b, c, d]

assert_eq(drive(sends(), [10, 11, 12]), ([0, 1, 2], [(0, 10), (1, 11), (2, 12), "end"]))
assert_eq(log, [("before", 0), ("sent", "x"), ("before", 1), ("sent", None), ("before", 2), ("sent", None)])

# An async for takes its items the same way; its end runs the else clause.
async def loop():
    out = []
    async for item in counter(2): out.append(item)
    else: out.append("else")
    return out

assert_eq(drive(loop()), ([0, 1], [(0, None), (1, None), "else"]))

# A break leaves the generator suspended at its yield; a later asend resumes it.
async def broken():
    g = counter(3)
    async for item in g:
        break
    return item, await g.asend("later")

log.clear()
assert_eq(drive(broken()), ([0, 1], ((0, None), (1, None))))
assert_eq(log, [("before", 0), ("sent", "later"), ("before", 1)])

# A just-started generator takes only None.
async def started():
    g = counter(1)
    try: await g.asend(1)
    except TypeError as e: return str(e)

assert_eq(drive(started()), ([], "can't send non-None value to a just-started async generator"))

# An error in the body propagates, and the ended generator stops.
async def failing():
    await Pause("f")
    yield 1
    raise ValueError("bad")

async def fails():
    g = failing()
    out = [await anext(g)]
    try: await anext(g)
    except ValueError as e: out.append(str(e))
    try: await g.asend(None)
    except StopAsyncIteration: out.append("stopped")
    return out

assert_eq(drive(fails()), (["f"], [1, "bad", "stopped"]))

# A StopAsyncIteration the body raises becomes a RuntimeError.
async def raising():
    yield 1
    raise StopAsyncIteration

async def raises():
    g = raising()
    await anext(g)
    try: await anext(g)
    except RuntimeError as e: return str(e), type(e.__cause__).__name__

assert_eq(drive(raises()), ([], ("async generator raised StopAsyncIteration", "StopAsyncIteration")))

# An awaited asend cannot be awaited again.
async def reused():
    g = counter(2)
    op = g.asend(None)
    first = await op
    try: await op
    except RuntimeError as e: return first, str(e)

assert_eq(drive(reused()), ([0], ((0, None), "cannot reuse already awaited __anext__()/asend()")))

# While one await of the generator is suspended in its body, another raises;
# the driver's cr_await is the asend object.
g = counter(2)
async def one(): return await g.asend(None)
async def other():
    try: await anext(g)
    except RuntimeError as e: return str(e)

co = one()
assert_eq(co.send(None), 0)
assert_eq(type(co.cr_await).__name__, "async_generator_asend")
assert_eq(drive(other()), ([], "anext(): asynchronous generator is already running"))
try: co.send(5)
except StopIteration as e: assert_eq(e.value, (0, 5))
assert_is(co.cr_await, None)

# A throw into the driver reaches the body at its await, and a yield there
# finishes the driver's await; a close closes the body.
async def catching():
    try: await Pause("t")
    except KeyError as e: yield ("caught", e.args[0])
    finally: log.append("finally")

async def awaits(g): return await anext(g)

co = awaits(catching())
assert_eq(co.send(None), "t")
try: co.throw(KeyError("k"))
except StopIteration as e: assert_eq(e.value, ("caught", "k"))

co = awaits(catching())
log.clear()
assert_eq(co.send(None), "t")
co.close()
assert_eq(log, ["finally"])

# Inside functions and generators, an await of one async generator's asend
# within another's body.
async def outer():
    async for x in counter(2):
        yield await counter(1).asend(None), x

async def collect():
    return [item async for item in outer()]

assert_eq(drive(collect()), ([0, 0, 1, 0], [((0, None), (0, None)), ((0, None), (1, None))]))
