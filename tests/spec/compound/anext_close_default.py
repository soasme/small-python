# spec: PLS-315 19.3.4, 13.16.3
# description: close() or a throw of GeneratorExit into a coroutine
# suspended in an await of anext() with a default, of an iterator whose
# __anext__ coroutine answers GeneratorExit with StopAsyncIteration, gives
# that await the default, and the coroutine runs on: its return ends
# close() with the value and the throw with StopIteration, and another
# await is a RuntimeError.
from harness import *
log = []
class Fut:
    def __await__(self):
        yield "fut"
class Ending:
    def __aiter__(self): return self
    async def __anext__(self):
        try: await Fut()
        except GeneratorExit: raise StopAsyncIteration
async def takes(default):
    got = await anext(Ending(), default)
    log.append(("took", got))
    return got
async def awaits_again():
    got = await anext(Ending(), "d")
    log.append(("took", got))
    await Fut()
def run(c, how):
    assert_eq(c.send(None), "fut")
    try: r = c.close() if how == "close" else c.throw(GeneratorExit)
    except BaseException as e: r = (type(e).__name__, e.args)
    return r
assert_eq([run(takes("d"), "close"), run(takes(None), "close"), run(takes("d"), "throw"), run(awaits_again(), "close")],
          ["d", None, ("StopIteration", ("d",)), ("RuntimeError", ("coroutine ignored GeneratorExit",))])
assert_eq(log, [("took", "d"), ("took", None), ("took", "d"), ("took", "d")])
# So does an __anext__ returning an awaitable whose Python __await__,
# called anew at each step, gives one such generator.
def ending():
    try: yield "fut"
    except GeneratorExit: raise StopAsyncIteration
class EndingAwait:
    def __init__(self): self.iterator = ending()
    def __await__(self): return self.iterator
class EndingInstance:
    def __aiter__(self): return self
    def __anext__(self):
        self.awaitable = getattr(self, "awaitable", None) or EndingAwait()
        return self.awaitable
async def takes_instance():
    got = await anext(EndingInstance(), "i")
    log.append(("took", got))
    return got
log.clear()
assert_eq((run(takes_instance(), "close"), run(takes_instance(), "throw"), log), ("i", ("StopIteration", ("i",)), [("took", "i"), ("took", "i")]))
