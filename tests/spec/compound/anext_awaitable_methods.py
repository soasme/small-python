# spec: PLS-315 19.3.4
# description: the iterator an anext() awaitable's __await__ returns, for
# an async generator suspended in an await whose __await__ is a Python
# generator, resumes it by next(), __next__, send, throw and close: a
# yield of the generator is its StopIteration, its end the default; a
# throw of a class with a Python __init__, or of an instance, raises in the
# generator; the awaitable once ended cannot be reused.
from harness import *

class Pause:
    def __init__(self, v): self.v = v
    def __await__(self):
        for _ in (): pass
        return (yield self.v)

class Caught(Exception):
    def __init__(self, *args): super().__init__("caught", *args)

log = []
async def agen():
    try:
        log.append(("sent", await Pause(1)))
    except Caught as e:
        log.append(e.args)
        await Pause(2)
    return
    yield

async def yields():
    await Pause(1)
    yield "item"

def run(source, *steps):
    out = []
    it = anext(source(), "default").__await__()
    for step in steps:
        try:
            out.append(step(it))
        except StopIteration as e:
            out.append(("stop", e.value))
        except BaseException as e:
            out.append((type(e).__name__, str(e)))
    return out

reuse = ("RuntimeError", "cannot reuse already awaited __anext__()/asend()")
assert_eq(run(agen, lambda g: g.send(None), lambda g: g.send("x"), lambda g: g.send(None)),
          [1, ("stop", "default"), reuse])
assert_eq(run(agen, next, lambda g: g.throw(Caught), lambda g: g.send(None)),
          [1, 2, ("stop", "default")])
assert_eq(run(agen, lambda g: g.__next__(), lambda g: g.throw(Caught(4)), lambda g: g.throw(Caught("again"))),
          [1, 2, ("Caught", "('caught', 'again')")])
assert_eq(run(agen, next, lambda g: g.throw(KeyError("k")), next), [1, ("KeyError", "'k'"), reuse])
assert_eq(run(agen, next, lambda g: g.close(), lambda g: g.close(), next), [1, None, None, reuse])
assert_eq(run(agen, lambda g: g.send(1)), [("TypeError", "can't send non-None value to a just-started async generator")])
assert_eq(run(yields, next, next, next), [1, ("stop", "item"), reuse])
assert_eq(run(yields, next, lambda g: g.throw(Caught)), [1, ("Caught", "caught")])
assert_eq(log, [("sent", "x"), ("caught",), ("caught", 4)])
