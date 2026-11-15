# spec: PLS-315 13.2.6, 15.3.2
# description: An asynchronous comprehension or generator expression over
# an object whose __aiter__ is a Python function calls it once, in the
# enclosing scope, when the comprehension is evaluated: a generator
# expression before its first item is asked for. __aiter__ may loop; its
# exception propagates there, and a result without __anext__ raises
# TypeError. Inside functions as at module level.
from harness import *

log = []

class Source:
    def __init__(self, n, bad=None): self.n, self.bad = n, bad
    def __aiter__(self):
        for _ in range(2): pass
        log.append("aiter")
        if self.bad == "raise": raise LookupError("aiter")
        if self.bad == "result": return 5
        self.i = 0
        return self
    async def __anext__(self):
        if self.i == self.n: raise StopAsyncIteration
        self.i += 1
        return self.i

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

async def comprehensions():
    out = [[x async for x in Source(2)], {x async for x in Source(1)}, {x: x async for x in Source(1)}]
    g = (x * 10 async for x in Source(2))
    log.append("made")
    out.append([x async for x in g])
    return out

def drive(c):
    try:
        c.send(None)
    except StopIteration as e:
        return e.value

def results():
    del log[:]
    out = [drive(comprehensions()), error(lambda: (x async for x in Source(1, "raise"))),
           error(lambda: (x async for x in Source(1, "result")))]
    return out + [list(log)]

expected = [[[1, 2], {1}, {1: 1}, [10, 20]], ('LookupError', 'aiter'),
            ('TypeError', "'async for' received an object from __aiter__ that does not implement __anext__: int"),
            ['aiter', 'aiter', 'aiter', 'aiter', 'made', 'aiter', 'aiter']]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
