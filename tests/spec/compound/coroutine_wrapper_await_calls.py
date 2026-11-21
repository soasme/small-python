# spec: PLS-315 13.4, 27.4.2, 27.4.4, 13.16.3
# description: An await of the wrapper a coroutine's __await__ returns
# drives that coroutine: its sends, throws and close reach the
# coroutine, the awaiting coroutine's cr_await is the wrapper, the
# coroutine's own end ends the await, and a coroutine already finished
# through its wrapper cannot be awaited again.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Wrapper:
    def __init__(self, coro): self.coro = coro
    def __await__(self): return self.coro.__await__()
class FutureLike:
    def __await__(self):
        got = yield 'f'
        return got
class Marker(Exception): pass
async def coro1():
    try:
        return await FutureLike()
    except ZeroDivisionError:
        raise Marker
    except GeneratorExit:
        log.append('exit1'); raise
    finally:
        log.append('finally1')
async def coro2():
    try:
        return await Wrapper(coro1())
    finally:
        log.append('finally2')
def step(f, *a):
    try: return ('value', f(*a))
    except StopIteration as e: return ('stop', e.value)
    except BaseException as e: return (type(e).__name__, e.args)
c = coro2(); log.append(step(c.send, None))
log.append(type(c.cr_await).__name__)
log.append(step(c.send, 'spam'))
c = coro2(); c.send(None); log.append(step(c.throw, ZeroDivisionError))
c = coro2(); c.send(None); log.append(step(c.throw, KeyError('k')))
c = coro2(); c.send(None); log.append(step(c.close))
c = coro2(); c.send(None); w = c.cr_await; log.append((type(w).__name__, step(w.send, 'direct'), c.cr_await is w))
log.append(step(c.send, 'after'))
c = coro2(); c.send(None); del c; log.append('dropped')
async def gen_based():
    inner = coro1()
    r = await inner.__await__().__self__ if hasattr(inner.__await__(), '__self__') else None
c3 = coro1(); w3 = c3.__await__()
async def twice():
    return await Wrapper(c3)
d = twice(); log.append(step(d.send, None)); log.append(step(c3.send, None))
log.append(step(d.send, 'end'))
for x in log: emit(x)
EXPECTED = [
    "('value', 'f')",
    'coroutine_wrapper',
    'finally1',
    'finally2',
    "('stop', 'spam')",
    'finally1',
    'finally2',
    "('Marker', ())",
    'finally1',
    'finally2',
    "('KeyError', ('k',))",
    'exit1',
    'finally1',
    'finally2',
    "('value', None)",
    'finally1',
    "('coroutine_wrapper', ('stop', 'direct'), True)",
    'finally2',
    "('RuntimeError', ('cannot reuse already awaited coroutine',))",
    'exit1',
    'finally1',
    'finally2',
    'dropped',
    "('value', 'f')",
    'finally1',
    "('stop', None)",
    "('RuntimeError', ('cannot reuse already awaited coroutine',))",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
