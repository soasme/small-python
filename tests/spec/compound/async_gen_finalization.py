# spec: PLS-315 B.5, 27.5.4
# description: The host's firstiter and finalizer hooks for asynchronous generators, and aclose() when there is no finalizer.
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

hooks = host.async_gen_hooks()
saved = hooks
if hooks is not None:
    # Without installed hooks the pair is (None, None).
    host.set_async_gen_hooks(None, None)
    assert_eq(host.async_gen_hooks(), (None, None))

# No finalizer: an unreachable suspended generator is closed with aclose(),
# whose awaitable is driven to completion.
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
