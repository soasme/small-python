# spec: PLS-315 13.16.2, 15.3.2
# description: An async generator whose async for over another async
# generator follows its own yield statement awaits that generator's next
# item afresh: a suspension inside the inner generator reaches the driver,
# and the driver's next send resumes it there, not after the yield. An
# async for, an awaited coroutine and an asynchronous comprehension over
# the outer generator behave alike. Inside functions as at module level.
from harness import *

log = []

class Pause:
    def __init__(self, tag): self.tag = tag
    def __await__(self):
        got = yield self.tag
        return got

async def inner():
    for i in range(3):
        got = await Pause(i)
        for _ in range(2): pass
        log.append(("inner", i, got))
        yield i

async def outer():
    async for x in inner():
        yield x * 10
        log.append(("after", x))

async def looped():
    out = []
    async for y in outer(): out.append(y)
    return out

async def awaited():
    return await looped()

async def gathered():
    return [y async for y in outer()]

def drive(c):
    out, n = [], 0
    try:
        while True:
            out.append(c.send(None if not out else "s%d" % n)); n += 1
    except StopIteration as e:
        return out, e.value

def results():
    del log[:]
    return [drive(looped()), drive(awaited()), drive(gathered()), list(log)]

expected = [([0, 1, 2], [0, 10, 20]), ([0, 1, 2], [0, 10, 20]), ([0, 1, 2], [0, 10, 20]),
            [('inner', 0, 's1'), ('after', 0), ('inner', 1, 's2'), ('after', 1), ('inner', 2, 's3'), ('after', 2),
             ('inner', 0, 's1'), ('after', 0), ('inner', 1, 's2'), ('after', 1), ('inner', 2, 's3'), ('after', 2),
             ('inner', 0, 's1'), ('after', 0), ('inner', 1, 's2'), ('after', 1), ('inner', 2, 's3'), ('after', 2)]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
