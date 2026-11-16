# spec: PLS-315 13.2.6, 15.3.2
# description: An asynchronous comprehension awaited in a coroutine
# suspends that coroutine at each await of its source, its conditions and
# its element, an async generator's own awaits included: the driver's
# send() reaches the innermost await and its value is the await's result;
# throw() raises there, a handler in the async generator may go on, and an
# uncaught exception propagates out of the comprehension. A comprehension
# inside another's element, and a comprehension's own end, behave alike.
# Inside functions as at module level.
from harness import *

log = []

class Pause:
    def __init__(self, tag): self.tag = tag
    def __await__(self):
        got = yield self.tag
        return got

async def counter(n):
    for i in range(n):
        try:
            got = await Pause(("count", i))
        except KeyError as e:
            for _ in range(2): pass
            log.append(("caught", str(e)))
            got = "handled"
        yield i, got

async def double(x):
    return await Pause(("double", x)) * 2

async def comprehensions():
    flat = [item async for item in counter(2)]
    chosen = [await double(i) async for i, got in counter(3) if got != "skip"]
    nested = [[j async for j, _ in counter(i)] async for i, _ in counter(2)]
    return flat, chosen, nested

def drive(c, sends):
    out = []
    try:
        item = c.send(None)
        while True:
            out.append(item)
            how = sends.pop(0) if sends else 1
            item = c.throw(KeyError(how[1])) if isinstance(how, tuple) else c.send(how)
    except StopIteration as e:
        return out, e.value
    except Exception as e:
        return out, type(e).__name__, str(e)

def results():
    del log[:]
    plain = drive(comprehensions(), ["a", ("throw", "k"), "skip", 2, 3, 4, 5])
    raised = drive(comprehensions(), [("throw", "k"), "v", 1, ("throw", "x")])
    async def bad():
        return [1 / x async for x, _ in counter(2)]
    return [plain, raised, drive(bad(), []), list(log)]

expected = [([('count', 0), ('count', 1), ('count', 0), ('count', 1), ('double', 1), ('count', 2), ('double', 2),
              ('count', 0), ('count', 1), ('count', 0)],
             ([(0, 'a'), (1, 'handled')], [6, 10], [[], [0]])),
            ([('count', 0), ('count', 1), ('count', 0), ('double', 0)], 'KeyError', "'x'"),
            ([('count', 0)], 'ZeroDivisionError', 'division by zero'), [('caught', "'k'"), ('caught', "'k'")]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
