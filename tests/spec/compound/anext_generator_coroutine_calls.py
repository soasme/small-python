# spec: PLS-315 19.3.4
# description: An await of anext() of an async iterator whose __anext__
# is a generator with CO_ITERABLE_COROUTINE (types.coroutine) awaits that
# generator: its yields suspend the await, values sent reach it, its
# return is the value, its StopAsyncIteration the default or raised
# without one, and a throw or close reaches its handlers.
from harness import *

log = []
def coroutine(func):
    func.__code__ = func.__code__.replace(co_flags=func.__code__.co_flags | 0x100)
    return func
class It:
    def __init__(self): self.n = 0
    def __aiter__(self): return self
    @coroutine
    def __anext__(self):
        if False: yield "never"
        for _ in (): pass
        log.append(self.n)
        if self.n >= 2: raise StopAsyncIteration()
        self.n += 1
        return self.n
class Suspends:
    def __aiter__(self): return self
    @coroutine
    def __anext__(self):
        got = yield "pause"
        log.append(("got", got))
        if got == "stop": raise StopAsyncIteration
        if got == "bad": raise KeyError(got)
        return got
async def consume(it, default):
    out = []
    for _ in range(4):
        try: out.append(await anext(it, default) if default != "none" else await anext(it))
        except StopAsyncIteration: out.append("stop")
        except KeyError as e: out.append(("key", str(e)))
    return out
def drive(coro, sends=()):
    sends = list(sends)
    value = None
    try:
        while True:
            y = coro.send(value)
            value = sends.pop(0) if sends else None
    except StopIteration as e:
        return e.value
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
class Guarded:
    def __aiter__(self): return self
    @coroutine
    def __anext__(self):
        try:
            yield "pause"
        except KeyError as e:
            log.append(("caught", str(e)))
            return "recovered"
        finally:
            log.append("finally")
async def once(it):
    try:
        return await anext(it, "d")
    except ValueError as e:
        return ("value", str(e))
def thrown(exc):
    c = once(Guarded())
    c.send(None)
    try: c.throw(exc)
    except StopIteration as e: return e.value
def closed():
    c = once(Guarded())
    c.send(None)
    return c.close()
assert_eq(run(lambda: drive(consume(It(), "default"))), ([1, 2, "default", "default"], [0, 1, 2, 2]))
assert_eq(run(lambda: drive(consume(It(), "none"))), ([1, 2, "stop", "stop"], [0, 1, 2, 2]))
assert_eq(run(lambda: drive(consume(Suspends(), "d"), ["a", "stop", "bad", "b"])),
          (["a", "d", ("key", "'bad'"), "b"], [("got", "a"), ("got", "stop"), ("got", "bad"), ("got", "b")]))
assert_eq([run(lambda: thrown(KeyError("k"))), run(lambda: thrown(ValueError("v"))), run(closed)],
          [("recovered", [("caught", "'k'"), "finally"]), (("value", "v"), ["finally"]), (None, ["finally"])])
