# spec: PLS-315 B.5, 27.5.4
# description: The host's firstiter and finalizer hooks for asynchronous generators, and closing without a finalizer.
from harness import *

def step(awaitable):
    """Drive an awaitable that does not suspend; return its result."""
    try:
        awaitable.send(None)
    except StopIteration as e:
        return e.value
    fail("the awaitable suspended")

log = []
async def agen(name):
    try:
        yield 1
        yield 2
    finally:
        log.append(("finally", name))

async def awaiting_cleanup():
    try:
        yield 1
    finally:
        await sleep_zero()
        log.append(("finally", "awaiting"))

class sleep_zero:
    def __await__(self):
        return
        yield

class suspend:
    def __await__(self):
        yield

async def suspending_cleanup():
    try:
        yield 1
    finally:
        log.append("before")
        await suspend()
        log.append("after")

hooks = host.async_gen_hooks()
saved = hooks
if hooks is not None:
    # Without installed hooks the pair is (None, None).
    host.set_async_gen_hooks(None, None)
    assert_eq(host.async_gen_hooks(), (None, None))

# No finalizer: an unreachable suspended generator is closed once, as close()
# closes a generator: an await that completes at once lets cleanup finish, one
# that suspends is not resumed.
g = agen("plain")
assert_eq(step(g.__anext__()), 1)
del g
host.collect()
assert_eq(log, [("finally", "plain")])
log.clear()
g = awaiting_cleanup()
assert_eq(step(g.__anext__()), 1)
del g
host.collect()
assert_eq(log, [("finally", "awaiting")])
log.clear()
g = suspending_cleanup()
assert_eq(step(g.__anext__()), 1)
del g
host.collect()
assert_eq(log, ["before"])
log.clear()
# Collected while its __anext__() awaitable is suspended in an await, the
# generator is closed without the "already running" check of aclose().
async def awaits_first():
    try:
        await suspend()
        yield 1
    finally:
        log.append("closed")
g = awaits_first()
awaiting = g.__anext__()
assert_eq(awaiting.send(None), None)
del g, awaiting
host.collect()
assert_eq(log, ["closed"])
log.clear()
# Cleanup may call functions; a body that yields again while closing is not
# resumed after that yield; an async for left by break closes its
# generator once nothing else holds it; inside functions as at module level.
def note(x):
    log.append(x)
    return x
async def calling():
    try:
        for i in range(3): yield i
    finally:
        note([note(j) for j in range(2)])
async def stubborn():
    try:
        yield 1
    finally:
        log.append("first")
        yield 2
        log.append("never")
def collect_both():
    g = calling()
    assert_eq(step(g.__anext__()), 0)
    del g
    host.collect()
    g = stubborn()
    assert_eq(step(g.__anext__()), 1)
    del g
    host.collect()
collect_both()
assert_eq(log, [0, 1, [0, 1], "first"])
log.clear()
async def breaking():
    async for x in calling():
        break
    log.append("after")
    return x
assert_eq(step(breaking()), 0)
host.collect()
assert_eq(log, [0, 1, [0, 1], "after"])
log.clear()
# A generator never started, or already finished, has nothing to close.
g = agen("unstarted")
del g
host.collect()
assert_eq(log, [])

if hooks is not None:
    first, finalized = [], []
    host.set_async_gen_hooks(first.append, finalized.append)
    try:
        g = agen("hooked")
        assert_eq(first, [])
        assert_eq(step(g.__anext__()), 1)
        assert_eq(len(first), 1)
        assert_is(first[0], g)
        step(g.__anext__())
        assert_eq(len(first), 1)
        first.clear()
        # With a finalizer, the finalizer is called instead of aclose().
        del g
        host.collect()
        assert_eq(len(finalized), 1)
        assert_eq(log, [])
        step(finalized.pop().aclose())
        assert_eq(log, [("finally", "hooked")])
    finally:
        host.set_async_gen_hooks(*saved)
