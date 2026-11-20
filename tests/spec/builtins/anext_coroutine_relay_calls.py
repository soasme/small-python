# spec: PLS-315 19.3.4, 27.5.1
# description: The awaitable anext() makes of an asynchronous iterator
# whose __anext__ returns a coroutine relays its send, __next__, next(),
# throw and close to that coroutine, bound, starred or called directly:
# a value the coroutine yields is the call's; its StopAsyncIteration is
# StopIteration of the default when one was given; its other exceptions,
# and a reuse once it ended, propagate.
from harness import assert_eq

log = []
class Pause:
    def __await__(self):
        v = yield "waiting"
        return v
class It:
    def __init__(self, mode): self.mode = mode
    def __aiter__(self): return self
    async def __anext__(self):
        try:
            got = await Pause()
            log.append(("got", got))
        except KeyError as e:
            log.append(("caught", repr(e)))
            if self.mode == "reraise": raise
            if self.mode == "pause": await Pause()
        except GeneratorExit:
            log.append("exit")
            if self.mode == "pause": await Pause()
            raise
        finally:
            for _ in (): pass
            log.append("finally")
        if self.mode == "stop": raise StopAsyncIteration
        if self.mode == "fail": raise LookupError("anext")
        return "value"
def show(f):
    try: r = ("ok", f())
    except BaseException as e: r = (type(e).__name__, getattr(e, "value", None) if isinstance(e, StopIteration) else str(e)[:40])
    out = (r, list(log)); del log[:]
    return out
def ops(mode, default):
    def mk():
        return anext(It(mode), default) if default != "none" else anext(It(mode))
    yield "send-send", lambda: (lambda op: (op.send(None), op.send(5)))(mk())
    yield "next-next", lambda: (lambda op: (next(op), next(op)))(mk())
    yield "dnext", lambda: (lambda op: (op.__next__(), op.__next__()))(mk())
    yield "throw", lambda: (lambda op: (op.send(None), op.throw(KeyError("k"))))(mk())
    yield "throw-fresh", lambda: mk().throw(KeyError("k"))
    yield "close", lambda: (lambda op: (op.send(None), op.close()))(mk())
    yield "close-fresh", lambda: mk().close()
    yield "send-fresh-value", lambda: mk().send(3)
    yield "reuse", lambda: (lambda op: (show(lambda: (op.send(None), op.send(1))), op.send(2)))(mk())
    yield "bound", lambda: (lambda op: (op.send(None), getattr(op, "send")(9)))(mk())
    yield "star", lambda: (lambda op: (op.send(*[None]), op.send(*[4])))(mk())
CASES = {
    ('plain', 'none', 'send-send'): (('StopIteration', 'value'), [('got', 5), 'finally']),
    ('plain', 'none', 'next-next'): (('TypeError', "'coroutine' object is not an iterator"), []),
    ('plain', 'none', 'dnext'): (('AttributeError', "'coroutine' object has no attribute '__n"), []),
    ('plain', 'none', 'throw'): (('StopIteration', 'value'), [('caught', "KeyError('k')"), 'finally']),
    ('plain', 'none', 'throw-fresh'): (('KeyError', "'k'"), []),
    ('plain', 'none', 'close'): (('ok', ('waiting', None)), ['exit', 'finally']),
    ('plain', 'none', 'close-fresh'): (('ok', None), []),
    ('plain', 'none', 'send-fresh-value'): (('TypeError', "can't send non-None value to a just-star"), []),
    ('plain', 'none', 'reuse'): (('RuntimeError', 'cannot reuse already awaited coroutine'), []),
    ('plain', 'none', 'bound'): (('StopIteration', 'value'), [('got', 9), 'finally']),
    ('plain', 'none', 'star'): (('StopIteration', 'value'), [('got', 4), 'finally']),
    ('plain', 'dflt', 'send-send'): (('StopIteration', 'value'), [('got', 5), 'finally']),
    ('plain', 'dflt', 'next-next'): (('StopIteration', 'value'), [('got', None), 'finally']),
    ('plain', 'dflt', 'dnext'): (('StopIteration', 'value'), [('got', None), 'finally']),
    ('plain', 'dflt', 'throw'): (('StopIteration', 'value'), [('caught', "KeyError('k')"), 'finally']),
    ('plain', 'dflt', 'throw-fresh'): (('KeyError', "'k'"), []),
    ('plain', 'dflt', 'close'): (('ok', ('waiting', None)), ['exit', 'finally']),
    ('plain', 'dflt', 'close-fresh'): (('ok', None), []),
    ('plain', 'dflt', 'send-fresh-value'): (('TypeError', "can't send non-None value to a just-star"), []),
    ('plain', 'dflt', 'reuse'): (('RuntimeError', 'cannot reuse already awaited coroutine'), []),
    ('plain', 'dflt', 'bound'): (('StopIteration', 'value'), [('got', 9), 'finally']),
    ('plain', 'dflt', 'star'): (('StopIteration', 'value'), [('got', 4), 'finally']),
    ('stop', 'none', 'send-send'): (('StopAsyncIteration', ''), [('got', 5), 'finally']),
    ('stop', 'none', 'next-next'): (('TypeError', "'coroutine' object is not an iterator"), []),
    ('stop', 'none', 'dnext'): (('AttributeError', "'coroutine' object has no attribute '__n"), []),
    ('stop', 'none', 'throw'): (('StopAsyncIteration', ''), [('caught', "KeyError('k')"), 'finally']),
    ('stop', 'none', 'throw-fresh'): (('KeyError', "'k'"), []),
    ('stop', 'none', 'close'): (('ok', ('waiting', None)), ['exit', 'finally']),
    ('stop', 'none', 'close-fresh'): (('ok', None), []),
    ('stop', 'none', 'send-fresh-value'): (('TypeError', "can't send non-None value to a just-star"), []),
    ('stop', 'none', 'reuse'): (('RuntimeError', 'cannot reuse already awaited coroutine'), []),
    ('stop', 'none', 'bound'): (('StopAsyncIteration', ''), [('got', 9), 'finally']),
    ('stop', 'none', 'star'): (('StopAsyncIteration', ''), [('got', 4), 'finally']),
    ('stop', 'dflt', 'send-send'): (('StopIteration', 'dflt'), [('got', 5), 'finally']),
    ('stop', 'dflt', 'next-next'): (('StopIteration', 'dflt'), [('got', None), 'finally']),
    ('stop', 'dflt', 'dnext'): (('StopIteration', 'dflt'), [('got', None), 'finally']),
    ('stop', 'dflt', 'throw'): (('StopIteration', 'dflt'), [('caught', "KeyError('k')"), 'finally']),
    ('stop', 'dflt', 'throw-fresh'): (('KeyError', "'k'"), []),
    ('stop', 'dflt', 'close'): (('ok', ('waiting', None)), ['exit', 'finally']),
    ('stop', 'dflt', 'close-fresh'): (('ok', None), []),
    ('stop', 'dflt', 'send-fresh-value'): (('TypeError', "can't send non-None value to a just-star"), []),
    ('stop', 'dflt', 'reuse'): (('RuntimeError', 'cannot reuse already awaited coroutine'), []),
    ('stop', 'dflt', 'bound'): (('StopIteration', 'dflt'), [('got', 9), 'finally']),
    ('stop', 'dflt', 'star'): (('StopIteration', 'dflt'), [('got', 4), 'finally']),
    ('fail', 'none', 'send-send'): (('LookupError', 'anext'), [('got', 5), 'finally']),
    ('fail', 'none', 'next-next'): (('TypeError', "'coroutine' object is not an iterator"), []),
    ('fail', 'none', 'dnext'): (('AttributeError', "'coroutine' object has no attribute '__n"), []),
    ('fail', 'none', 'throw'): (('LookupError', 'anext'), [('caught', "KeyError('k')"), 'finally']),
    ('fail', 'none', 'throw-fresh'): (('KeyError', "'k'"), []),
    ('fail', 'none', 'close'): (('ok', ('waiting', None)), ['exit', 'finally']),
    ('fail', 'none', 'close-fresh'): (('ok', None), []),
    ('fail', 'none', 'send-fresh-value'): (('TypeError', "can't send non-None value to a just-star"), []),
    ('fail', 'none', 'reuse'): (('RuntimeError', 'cannot reuse already awaited coroutine'), []),
    ('fail', 'none', 'bound'): (('LookupError', 'anext'), [('got', 9), 'finally']),
    ('fail', 'none', 'star'): (('LookupError', 'anext'), [('got', 4), 'finally']),
    ('fail', 'dflt', 'send-send'): (('LookupError', 'anext'), [('got', 5), 'finally']),
    ('fail', 'dflt', 'next-next'): (('LookupError', 'anext'), [('got', None), 'finally']),
    ('fail', 'dflt', 'dnext'): (('LookupError', 'anext'), [('got', None), 'finally']),
    ('fail', 'dflt', 'throw'): (('LookupError', 'anext'), [('caught', "KeyError('k')"), 'finally']),
    ('fail', 'dflt', 'throw-fresh'): (('KeyError', "'k'"), []),
    ('fail', 'dflt', 'close'): (('ok', ('waiting', None)), ['exit', 'finally']),
    ('fail', 'dflt', 'close-fresh'): (('ok', None), []),
    ('fail', 'dflt', 'send-fresh-value'): (('TypeError', "can't send non-None value to a just-star"), []),
    ('fail', 'dflt', 'reuse'): (('RuntimeError', 'cannot reuse already awaited coroutine'), []),
    ('fail', 'dflt', 'bound'): (('LookupError', 'anext'), [('got', 9), 'finally']),
    ('fail', 'dflt', 'star'): (('LookupError', 'anext'), [('got', 4), 'finally']),
    ('reraise', 'none', 'send-send'): (('StopIteration', 'value'), [('got', 5), 'finally']),
    ('reraise', 'none', 'next-next'): (('TypeError', "'coroutine' object is not an iterator"), []),
    ('reraise', 'none', 'dnext'): (('AttributeError', "'coroutine' object has no attribute '__n"), []),
    ('reraise', 'none', 'throw'): (('KeyError', "'k'"), [('caught', "KeyError('k')"), 'finally']),
    ('reraise', 'none', 'throw-fresh'): (('KeyError', "'k'"), []),
    ('reraise', 'none', 'close'): (('ok', ('waiting', None)), ['exit', 'finally']),
    ('reraise', 'none', 'close-fresh'): (('ok', None), []),
    ('reraise', 'none', 'send-fresh-value'): (('TypeError', "can't send non-None value to a just-star"), []),
    ('reraise', 'none', 'reuse'): (('RuntimeError', 'cannot reuse already awaited coroutine'), []),
    ('reraise', 'none', 'bound'): (('StopIteration', 'value'), [('got', 9), 'finally']),
    ('reraise', 'none', 'star'): (('StopIteration', 'value'), [('got', 4), 'finally']),
    ('reraise', 'dflt', 'send-send'): (('StopIteration', 'value'), [('got', 5), 'finally']),
    ('reraise', 'dflt', 'next-next'): (('StopIteration', 'value'), [('got', None), 'finally']),
    ('reraise', 'dflt', 'dnext'): (('StopIteration', 'value'), [('got', None), 'finally']),
    ('reraise', 'dflt', 'throw'): (('KeyError', "'k'"), [('caught', "KeyError('k')"), 'finally']),
    ('reraise', 'dflt', 'throw-fresh'): (('KeyError', "'k'"), []),
    ('reraise', 'dflt', 'close'): (('ok', ('waiting', None)), ['exit', 'finally']),
    ('reraise', 'dflt', 'close-fresh'): (('ok', None), []),
    ('reraise', 'dflt', 'send-fresh-value'): (('TypeError', "can't send non-None value to a just-star"), []),
    ('reraise', 'dflt', 'reuse'): (('RuntimeError', 'cannot reuse already awaited coroutine'), []),
    ('reraise', 'dflt', 'bound'): (('StopIteration', 'value'), [('got', 9), 'finally']),
    ('reraise', 'dflt', 'star'): (('StopIteration', 'value'), [('got', 4), 'finally']),
    ('pause', 'none', 'send-send'): (('StopIteration', 'value'), [('got', 5), 'finally']),
    ('pause', 'none', 'next-next'): (('TypeError', "'coroutine' object is not an iterator"), []),
    ('pause', 'none', 'dnext'): (('AttributeError', "'coroutine' object has no attribute '__n"), []),
    ('pause', 'none', 'throw'): (('ok', ('waiting', 'waiting')), [('caught', "KeyError('k')"), 'finally']),
    ('pause', 'none', 'throw-fresh'): (('KeyError', "'k'"), []),
    ('pause', 'none', 'close'): (('RuntimeError', 'coroutine ignored GeneratorExit'), ['exit', 'finally']),
    ('pause', 'none', 'close-fresh'): (('ok', None), []),
    ('pause', 'none', 'send-fresh-value'): (('TypeError', "can't send non-None value to a just-star"), []),
    ('pause', 'none', 'reuse'): (('RuntimeError', 'cannot reuse already awaited coroutine'), []),
    ('pause', 'none', 'bound'): (('StopIteration', 'value'), [('got', 9), 'finally']),
    ('pause', 'none', 'star'): (('StopIteration', 'value'), [('got', 4), 'finally']),
    ('pause', 'dflt', 'send-send'): (('StopIteration', 'value'), [('got', 5), 'finally']),
    ('pause', 'dflt', 'next-next'): (('StopIteration', 'value'), [('got', None), 'finally']),
    ('pause', 'dflt', 'dnext'): (('StopIteration', 'value'), [('got', None), 'finally']),
    ('pause', 'dflt', 'throw'): (('ok', ('waiting', 'waiting')), [('caught', "KeyError('k')"), 'finally']),
    ('pause', 'dflt', 'throw-fresh'): (('KeyError', "'k'"), []),
    ('pause', 'dflt', 'close'): (('RuntimeError', 'coroutine ignored GeneratorExit'), ['exit', 'finally']),
    ('pause', 'dflt', 'close-fresh'): (('ok', None), []),
    ('pause', 'dflt', 'send-fresh-value'): (('TypeError', "can't send non-None value to a just-star"), []),
    ('pause', 'dflt', 'reuse'): (('RuntimeError', 'cannot reuse already awaited coroutine'), []),
    ('pause', 'dflt', 'bound'): (('StopIteration', 'value'), [('got', 9), 'finally']),
    ('pause', 'dflt', 'star'): (('StopIteration', 'value'), [('got', 4), 'finally']),
}
assert_eq(len(CASES), 110)
for (mode, default, name), expected in CASES.items():
    assert_eq(show(dict(ops(mode, default))[name]), expected, f"{mode} {default} {name}")
