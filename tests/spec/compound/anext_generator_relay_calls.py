# spec: PLS-315 19.3.4, 27.4.5, 27.5.1
# description: An anext() awaitable's send, __next__ and throw, bound or
# through its type, step what __anext__ returned: an async generator's
# asend, a coroutine, or a generator whose code is an iterable coroutine,
# whose suspension passes out and whose return ends the awaitable with
# StopIteration of its value.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
def spin():
    for _ in (): pass
async def agen():
    spin(); log.append('agen'); yield 1
class MyAsyncIter:
    def __aiter__(self): return self
    async def __anext__(self):
        spin(); log.append('coro'); return 1
class Gen:
    def __aiter__(self): return self
    def __anext__(self): return self.gen()
def gen(self):
    spin(); log.append('gen')
    yield 'paused'
    return 1
gen.__code__ = gen.__code__.replace(co_flags=gen.__code__.co_flags | 0x100)
Gen.gen = gen
def step(f, *a):
    try: return ('value', f(*a))
    except StopIteration as e: return ('stop', e.value)
    except BaseException as e: return (type(e).__name__, e.args)
for make in (agen, MyAsyncIter, Gen):
    for how in ('send', 'next', 'type_send', 'throw'):
        aw = anext(make(), 'completed')
        f = {'send': lambda: aw.send(None), 'next': lambda: aw.__next__(), 'type_send': lambda: type(aw).send(aw, None),
             'throw': lambda: aw.throw(KeyError('k'))}[how]
        log.append((make.__name__, how, step(f)))
        log.append((make.__name__, how, 'again', step(lambda: aw.send(None))))
for x in log: emit(x)
EXPECTED = [
    'agen',
    "('agen', 'send', ('stop', 1))",
    "('agen', 'send', 'again', ('RuntimeError', ('cannot reuse already awaited __anext__()/asend()',)))",
    'agen',
    "('agen', 'next', ('stop', 1))",
    "('agen', 'next', 'again', ('RuntimeError', ('cannot reuse already awaited __anext__()/asend()',)))",
    'agen',
    "('agen', 'type_send', ('stop', 1))",
    "('agen', 'type_send', 'again', ('RuntimeError', ('cannot reuse already awaited __anext__()/asend()',)))",
    "('agen', 'throw', ('KeyError', ('k',)))",
    "('agen', 'throw', 'again', ('RuntimeError', ('cannot reuse already awaited __anext__()/asend()',)))",
    'coro',
    "('MyAsyncIter', 'send', ('stop', 1))",
    "('MyAsyncIter', 'send', 'again', ('RuntimeError', ('cannot reuse already awaited coroutine',)))",
    'coro',
    "('MyAsyncIter', 'next', ('stop', 1))",
    "('MyAsyncIter', 'next', 'again', ('RuntimeError', ('cannot reuse already awaited coroutine',)))",
    'coro',
    "('MyAsyncIter', 'type_send', ('stop', 1))",
    "('MyAsyncIter', 'type_send', 'again', ('RuntimeError', ('cannot reuse already awaited coroutine',)))",
    "('MyAsyncIter', 'throw', ('KeyError', ('k',)))",
    "('MyAsyncIter', 'throw', 'again', ('RuntimeError', ('cannot reuse already awaited coroutine',)))",
    'gen',
    "('Gen', 'send', ('value', 'paused'))",
    "('Gen', 'send', 'again', ('stop', 1))",
    'gen',
    "('Gen', 'next', ('value', 'paused'))",
    "('Gen', 'next', 'again', ('stop', 1))",
    'gen',
    "('Gen', 'type_send', ('value', 'paused'))",
    "('Gen', 'type_send', 'again', ('stop', 1))",
    "('Gen', 'throw', ('KeyError', ('k',)))",
    "('Gen', 'throw', 'again', ('stop', None))",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
