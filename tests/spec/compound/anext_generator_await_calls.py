# spec: PLS-315 19.3.4 27.5.1 13.4.1
# description: An await of anext() of an async generator, with a default
# or not, resumes the generator: what its awaits pass out reaches the
# coroutine's driver, a yield is the await's value, and its end gives the
# default, or raises StopAsyncIteration; an error it raises is the
# await's. While the await is suspended, the coroutine's cr_await is the
# anext() awaitable, its generator is running, and a throw into the
# coroutine raises inside the generator, a close closing it.
from harness import *

class Pause:
    def __init__(self, v): self.v = v
    def __await__(self):
        got = yield ("pause", self.v)
        return (self.v, got)

async def values(fail=False):
    try:
        yield await Pause(1)
        yield 2
        if fail: raise KeyError("k")
    except ValueError as e:
        yield ("handled", e.args)

async def run(fail=False):
    g = values(fail)
    out = [await anext(g, "default"), await anext(g)]
    try:
        out.append(await anext(g, "default"))
        out.append(await anext(g))
    except StopAsyncIteration:
        out.append("stop")
    except KeyError as e:
        out.append(("key", e.args))
    return out

def drive(coroutine, sent="s"):
    passed = []
    try:
        passed.append(coroutine.send(None))
        while True: passed.append(coroutine.send(sent))
    except StopIteration as e:
        return passed, e.value

def suspended():
    g = values()
    async def one(): return await anext(g, "default")
    c = one()
    first = c.send(None)
    state = [type(c.cr_await).__name__, g.ag_running]
    try:
        c.throw(ValueError("v"))
    except StopIteration as e:
        state.append(e.value)
    state.append(g.ag_running)
    h = values()
    async def two(): return await anext(h, "default")
    c = two()
    c.send(None)
    state.append((c.close(), h.ag_running, h.ag_frame is None))
    return first, state

def results():
    return [drive(run()), drive(run(True)), suspended()]

expected = [
    ([("pause", 1)], [(1, "s"), 2, "default", "stop"]),
    ([("pause", 1)], [(1, "s"), 2, ("key", ("k",))]),
    (("pause", 1), ["anext_awaitable", True, ("handled", ("v",)), False, (None, False, True)]),
]

assert_eq(results(), expected)
assert_eq(results(), expected)
