# spec: PLS-315 19.3.4, 13.4
# description: anext(it, default)'s awaitable calls close and throw on the
# iterator its __anext__ result's __await__ returns; when that is a
# list_iterator, which has neither, closing or throwing into the
# suspended coroutine raises AttributeError there, its finally runs, and
# the coroutine is then finished.
from harness import assert_eq

log = []

class Awaited:
    def __await__(self):
        for _ in (): pass
        return iter([1, 2])

class Source:
    def __aiter__(self): return self
    def __anext__(self): return Awaited()

async def co():
    try:
        return await anext(Source(), "d")
    finally:
        log.append("finally")

def attempt(f):
    try: return f()
    except Exception as e: return type(e).__name__, str(e)

def run():
    c = co()
    first = c.send(None)
    closed = attempt(c.close)
    after = attempt(lambda: c.send(None))
    c2 = co(); c2.send(None)
    thrown = attempt(lambda: c2.throw(KeyError("k")))
    return [first, closed, after, thrown, log]

assert_eq(run(), [1, ("AttributeError", "'list_iterator' object has no attribute 'close'"),
                  ("RuntimeError", "cannot reuse already awaited coroutine"),
                  ("AttributeError", "'list_iterator' object has no attribute 'throw'"), ["finally", "finally"]])
