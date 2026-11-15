# spec: PLS-315 15.3.2, 15.5.2
# description: An async for whose iterator's __anext__ is a Python async
# function awaits each coroutine it returns, which may loop, suspend at
# an await and raise StopAsyncIteration to end the loop or another
# exception that propagates; an async with awaits the coroutines of
# Python __aenter__ and __aexit__ alike, __aexit__'s true result
# suppressing the body's exception. Inside functions as at module level.
from harness import *

log = []

class Pause:
    def __await__(self):
        log.append("pause")
        return (yield "paused")

class Counter:
    def __init__(self, n, bad=False): self.i, self.n, self.bad = 0, n, bad
    def __aiter__(self): return self
    async def __anext__(self):
        for _ in range(2): pass
        if self.i == self.n:
            if self.bad: raise LookupError("anext")
            raise StopAsyncIteration
        self.i += 1
        await Pause()
        return self.i

class Manager:
    def __init__(self, swallow): self.swallow = swallow
    async def __aenter__(self):
        for _ in range(2): pass
        await Pause()
        log.append("enter")
        return "managed"
    async def __aexit__(self, kind, value, traceback):
        log.append(("exit", kind.__name__ if kind else None))
        await Pause()
        return self.swallow

async def body():
    out = []
    async for i in Counter(3):
        out.append(i)
    try:
        async for i in Counter(1, True):
            out.append(i)
    except LookupError as e:
        out.append(str(e))
    async with Manager(False) as v:
        out.append(v)
    async with Manager(True):
        raise KeyError("swallowed")
    out.append("after")
    return out

def drive(c):
    sent = 0
    try:
        while True:
            assert_eq(c.send(None), "paused")
            sent += 1
    except StopIteration as e:
        return e.value, sent

def results():
    del log[:]
    return [drive(body()), list(log)]

expected = [([1, 2, 3, 1, 'anext', 'managed', 'after'], 8),
            ['pause', 'pause', 'pause', 'pause', 'pause', 'enter', ('exit', None), 'pause', 'pause', 'enter',
             ('exit', 'KeyError'), 'pause']]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
