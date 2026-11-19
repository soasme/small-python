# spec: PLS-315 27.5.1, 27.4.2
# description: An asend(), athrow() or aclose() awaitable in progress, its
# async generator suspended in an await of its own: close(), or close
# from its type, throws GeneratorExit there; a value the generator yields,
# its return, or a StopIteration, StopAsyncIteration or GeneratorExit it
# raises end the close with None and the awaitable, whose next send raises
# StopIteration; an await it suspends in raises RuntimeError, the
# awaitable left running; a value an aclose()'s generator yields raises
# RuntimeError; another exception propagates. throw() raises its
# exception there as an asend()'s throw does, and send() resumes it.
# Made but not begun, close() and throw() throw at the generator's yield,
# beginning the awaitable, which ends as when begun. Inside functions as at
# module level.
from harness import *

log = []
class Pause:
    def __init__(self, v): self.v = v
    def __await__(self): return (yield self.v)

async def body(after):
    try:
        yield 1
    except ValueError:
        log.append("athrow")
    try:
        await Pause("p")
    except (GeneratorExit, KeyError) as e:
        for _ in range(2): pass
        log.append(type(e).__name__)
        if after == "yield": yield "kept"
        elif after == "await": await Pause("again")
        elif after == "raise": raise LookupError("l")
        elif after == "return": return
        elif after == "stop": raise StopAsyncIteration
        else: raise
    yield "end"

def show(f):
    try: return ("ok", f())
    except BaseException as e: return (type(e).__name__, str(e))

def case(kind, after, how, fresh):
    del log[:]
    g = body(after)
    try: g.asend(None).send(None)
    except StopIteration: pass
    a = g.asend(None) if kind == "asend" else g.athrow(ValueError) if kind == "athrow" else g.aclose()
    first = show(lambda: a.send(None)) if fresh == "sent" else None
    if how == "close": r = show(a.close)
    elif how == "type": r = show(lambda: type(a).close(a))
    else: r = show(lambda: a.throw(KeyError("k")))
    again = show(lambda: a.send(None))
    return first, r, again, log[:]

def run():
    out = []
    for kind in ("asend", "athrow", "aclose"):
        for after in ("yield", "await", "raise", "return", "stop", "reraise"):
            for how in ("close", "type", "throw"):
                out.extend((kind, after, how, fresh, case(kind, after, how, fresh)) for fresh in ("sent", "fresh"))
    return out


expected = [
    ('asend', 'yield', 'close', 'sent', (('ok', 'p'), ('ok', None), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), ['GeneratorExit'])),
    ('asend', 'yield', 'close', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), [])),
    ('asend', 'yield', 'type', 'sent', (('ok', 'p'), ('ok', None), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), ['GeneratorExit'])),
    ('asend', 'yield', 'type', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), [])),
    ('asend', 'yield', 'throw', 'sent', (('ok', 'p'), ('StopIteration', 'kept'), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), ['KeyError'])),
    ('asend', 'yield', 'throw', 'fresh', (None, ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), [])),
    ('asend', 'await', 'close', 'sent', (('ok', 'p'), ('RuntimeError', 'coroutine ignored GeneratorExit'), ('StopIteration', 'end'), ['GeneratorExit'])),
    ('asend', 'await', 'close', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), [])),
    ('asend', 'await', 'type', 'sent', (('ok', 'p'), ('RuntimeError', 'coroutine ignored GeneratorExit'), ('StopIteration', 'end'), ['GeneratorExit'])),
    ('asend', 'await', 'type', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), [])),
    ('asend', 'await', 'throw', 'sent', (('ok', 'p'), ('ok', 'again'), ('StopIteration', 'end'), ['KeyError'])),
    ('asend', 'await', 'throw', 'fresh', (None, ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), [])),
    ('asend', 'raise', 'close', 'sent', (('ok', 'p'), ('LookupError', 'l'), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), ['GeneratorExit'])),
    ('asend', 'raise', 'close', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), [])),
    ('asend', 'raise', 'type', 'sent', (('ok', 'p'), ('LookupError', 'l'), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), ['GeneratorExit'])),
    ('asend', 'raise', 'type', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), [])),
    ('asend', 'raise', 'throw', 'sent', (('ok', 'p'), ('LookupError', 'l'), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), ['KeyError'])),
    ('asend', 'raise', 'throw', 'fresh', (None, ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), [])),
    ('asend', 'return', 'close', 'sent', (('ok', 'p'), ('ok', None), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), ['GeneratorExit'])),
    ('asend', 'return', 'close', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), [])),
    ('asend', 'return', 'type', 'sent', (('ok', 'p'), ('ok', None), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), ['GeneratorExit'])),
    ('asend', 'return', 'type', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), [])),
    ('asend', 'return', 'throw', 'sent', (('ok', 'p'), ('StopAsyncIteration', ''), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), ['KeyError'])),
    ('asend', 'return', 'throw', 'fresh', (None, ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), [])),
    ('asend', 'stop', 'close', 'sent', (('ok', 'p'), ('RuntimeError', 'async generator raised StopAsyncIteration'), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), ['GeneratorExit'])),
    ('asend', 'stop', 'close', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), [])),
    ('asend', 'stop', 'type', 'sent', (('ok', 'p'), ('RuntimeError', 'async generator raised StopAsyncIteration'), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), ['GeneratorExit'])),
    ('asend', 'stop', 'type', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), [])),
    ('asend', 'stop', 'throw', 'sent', (('ok', 'p'), ('RuntimeError', 'async generator raised StopAsyncIteration'), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), ['KeyError'])),
    ('asend', 'stop', 'throw', 'fresh', (None, ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), [])),
    ('asend', 'reraise', 'close', 'sent', (('ok', 'p'), ('ok', None), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), ['GeneratorExit'])),
    ('asend', 'reraise', 'close', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), [])),
    ('asend', 'reraise', 'type', 'sent', (('ok', 'p'), ('ok', None), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), ['GeneratorExit'])),
    ('asend', 'reraise', 'type', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), [])),
    ('asend', 'reraise', 'throw', 'sent', (('ok', 'p'), ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), ['KeyError'])),
    ('asend', 'reraise', 'throw', 'fresh', (None, ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited __anext__()/asend()'), [])),
    ('athrow', 'yield', 'close', 'sent', (('ok', 'p'), ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ['athrow', 'GeneratorExit'])),
    ('athrow', 'yield', 'close', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('athrow', 'yield', 'type', 'sent', (('ok', 'p'), ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ['athrow', 'GeneratorExit'])),
    ('athrow', 'yield', 'type', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('athrow', 'yield', 'throw', 'sent', (('ok', 'p'), ('StopIteration', 'kept'), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ['athrow', 'KeyError'])),
    ('athrow', 'yield', 'throw', 'fresh', (None, ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('athrow', 'await', 'close', 'sent', (('ok', 'p'), ('RuntimeError', 'coroutine ignored GeneratorExit'), ('StopIteration', 'end'), ['athrow', 'GeneratorExit'])),
    ('athrow', 'await', 'close', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('athrow', 'await', 'type', 'sent', (('ok', 'p'), ('RuntimeError', 'coroutine ignored GeneratorExit'), ('StopIteration', 'end'), ['athrow', 'GeneratorExit'])),
    ('athrow', 'await', 'type', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('athrow', 'await', 'throw', 'sent', (('ok', 'p'), ('ok', 'again'), ('StopIteration', 'end'), ['athrow', 'KeyError'])),
    ('athrow', 'await', 'throw', 'fresh', (None, ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('athrow', 'raise', 'close', 'sent', (('ok', 'p'), ('LookupError', 'l'), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ['athrow', 'GeneratorExit'])),
    ('athrow', 'raise', 'close', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('athrow', 'raise', 'type', 'sent', (('ok', 'p'), ('LookupError', 'l'), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ['athrow', 'GeneratorExit'])),
    ('athrow', 'raise', 'type', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('athrow', 'raise', 'throw', 'sent', (('ok', 'p'), ('LookupError', 'l'), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ['athrow', 'KeyError'])),
    ('athrow', 'raise', 'throw', 'fresh', (None, ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('athrow', 'return', 'close', 'sent', (('ok', 'p'), ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ['athrow', 'GeneratorExit'])),
    ('athrow', 'return', 'close', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('athrow', 'return', 'type', 'sent', (('ok', 'p'), ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ['athrow', 'GeneratorExit'])),
    ('athrow', 'return', 'type', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('athrow', 'return', 'throw', 'sent', (('ok', 'p'), ('StopAsyncIteration', ''), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ['athrow', 'KeyError'])),
    ('athrow', 'return', 'throw', 'fresh', (None, ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('athrow', 'stop', 'close', 'sent', (('ok', 'p'), ('RuntimeError', 'async generator raised StopAsyncIteration'), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ['athrow', 'GeneratorExit'])),
    ('athrow', 'stop', 'close', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('athrow', 'stop', 'type', 'sent', (('ok', 'p'), ('RuntimeError', 'async generator raised StopAsyncIteration'), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ['athrow', 'GeneratorExit'])),
    ('athrow', 'stop', 'type', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('athrow', 'stop', 'throw', 'sent', (('ok', 'p'), ('RuntimeError', 'async generator raised StopAsyncIteration'), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ['athrow', 'KeyError'])),
    ('athrow', 'stop', 'throw', 'fresh', (None, ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('athrow', 'reraise', 'close', 'sent', (('ok', 'p'), ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ['athrow', 'GeneratorExit'])),
    ('athrow', 'reraise', 'close', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('athrow', 'reraise', 'type', 'sent', (('ok', 'p'), ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ['athrow', 'GeneratorExit'])),
    ('athrow', 'reraise', 'type', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('athrow', 'reraise', 'throw', 'sent', (('ok', 'p'), ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ['athrow', 'KeyError'])),
    ('athrow', 'reraise', 'throw', 'fresh', (None, ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'yield', 'close', 'sent', (('StopIteration', ''), ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'yield', 'close', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'yield', 'type', 'sent', (('StopIteration', ''), ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'yield', 'type', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'yield', 'throw', 'sent', (('StopIteration', ''), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'yield', 'throw', 'fresh', (None, ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'await', 'close', 'sent', (('StopIteration', ''), ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'await', 'close', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'await', 'type', 'sent', (('StopIteration', ''), ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'await', 'type', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'await', 'throw', 'sent', (('StopIteration', ''), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'await', 'throw', 'fresh', (None, ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'raise', 'close', 'sent', (('StopIteration', ''), ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'raise', 'close', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'raise', 'type', 'sent', (('StopIteration', ''), ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'raise', 'type', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'raise', 'throw', 'sent', (('StopIteration', ''), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'raise', 'throw', 'fresh', (None, ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'return', 'close', 'sent', (('StopIteration', ''), ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'return', 'close', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'return', 'type', 'sent', (('StopIteration', ''), ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'return', 'type', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'return', 'throw', 'sent', (('StopIteration', ''), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'return', 'throw', 'fresh', (None, ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'stop', 'close', 'sent', (('StopIteration', ''), ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'stop', 'close', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'stop', 'type', 'sent', (('StopIteration', ''), ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'stop', 'type', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'stop', 'throw', 'sent', (('StopIteration', ''), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'stop', 'throw', 'fresh', (None, ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'reraise', 'close', 'sent', (('StopIteration', ''), ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'reraise', 'close', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'reraise', 'type', 'sent', (('StopIteration', ''), ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'reraise', 'type', 'fresh', (None, ('ok', None), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'reraise', 'throw', 'sent', (('StopIteration', ''), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
    ('aclose', 'reraise', 'throw', 'fresh', (None, ('KeyError', "'k'"), ('RuntimeError', 'cannot reuse already awaited aclose()/athrow()'), [])),
]

assert_eq(run(), expected)

def main():
    return run()

assert_eq(main(), expected)
