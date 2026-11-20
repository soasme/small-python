# spec: PLS-315 19.3.4, 13.4
# description: The awaitable anext() makes with a default, of an
# __anext__ result whose class defines __await__, takes that __await__'s
# iterator anew at each __next__, send, throw or close, through next()
# and bound methods too, relaying to the iterator's method of that name,
# send also of None, its __next__ for __next__; a StopAsyncIteration
# becomes StopIteration of the default; a non-iterator from __await__ or
# its error propagates; awaited and inside a generator too. Awaited, a
# send of None is the iterator's __next__ and the coroutine's close the
# iterator's close, the coroutine's finally running after.
from harness import assert_eq

log = []
class GenAwait:
    def __init__(self, *steps): self.steps = steps
    def __await__(self):
        log.append('await')
        for s in self.steps:
            got = yield s
            log.append(('got', got))
        return 'done'
class StopAsync:
    def __await__(self):
        for _ in (): pass
        log.append('await')
        raise StopAsyncIteration
        yield
class It:
    def __init__(self): self.n = 0
    def __next__(self):
        for _ in (): pass
        self.n += 1
        log.append(('next', self.n))
        if self.n > 1: raise StopIteration(self.n)
        return self.n
    def send(self, v):
        for _ in (): pass
        log.append(('send', v)); return v
    def throw(self, *a):
        for _ in (): pass
        log.append(('throw', len(a))); raise StopAsyncIteration
    def close(self):
        for _ in (): pass
        log.append('close'); return 'c'
    def __iter__(self): return self
class PlainAwait:
    def __await__(self):
        for _ in (): pass
        log.append('await'); return It()
class BadAwait:
    def __await__(self):
        for _ in (): pass
        return 5
class RaiseAwait:
    def __await__(self):
        for _ in (): pass
        raise LookupError('aw')
class ListAwait:
    def __await__(self):
        for _ in (): pass
        return iter([1, 2])
class Src:
    def __init__(self, aw): self.aw = aw
    def __aiter__(self): return self
    def __anext__(self): return self.aw
def run(f):
    del log[:]
    try: r = f()
    except BaseException as e: r = (type(e).__name__, str(e), getattr(e, 'value', None))
    return r, log[:]
def aw(x): return anext(Src(x), 'dflt')
cases = [
 lambda: aw(GenAwait(1, 2)).send(None),
 lambda: (lambda a: (a.send(None), a.send(5)))(aw(GenAwait(1, 2))),
 lambda: aw(GenAwait()).send(None),
 lambda: aw(StopAsync()).send(None),
 lambda: next(aw(GenAwait(3))),
 lambda: aw(GenAwait(4)).__next__(),
 lambda: (lambda s: s(None))(aw(GenAwait(6)).send),
 lambda: aw(GenAwait(1)).throw(ValueError('t')),
 lambda: aw(GenAwait(1)).close(),
 lambda: aw(PlainAwait()).send(None),
 lambda: aw(PlainAwait()).send(7),
 lambda: aw(PlainAwait()).throw(ValueError),
 lambda: aw(PlainAwait()).close(),
 lambda: aw(BadAwait()).send(None),
 lambda: aw(RaiseAwait()).send(None),
 lambda: aw(ListAwait()).send(None),
 lambda: aw(ListAwait()).send(3),
 lambda: (lambda a: [a.send(None) for _ in range(1)])(aw(GenAwait(9))),
]
EXPECTED = [
    (1, ['await']),
    (('TypeError', "can't send non-None value to a just-started generator", None), ['await']),
    (('StopIteration', 'done', 'done'), ['await']),
    (('StopIteration', 'dflt', 'dflt'), ['await']),
    (3, ['await']),
    (4, ['await']),
    (6, ['await']),
    (('ValueError', 't', None), []),
    (None, []),
    (None, ['await', ('send', None)]),
    (7, ['await', ('send', 7)]),
    (('StopIteration', 'dflt', 'dflt'), ['await', ('throw', 1)]),
    ('c', ['await', 'close']),
    (('TypeError', 'BadAwait.__await__() must return an iterator, not int', None), []),
    (('LookupError', 'aw', None), []),
    (('AttributeError', "'list_iterator' object has no attribute 'send'", None), []),
    (('AttributeError', "'list_iterator' object has no attribute 'send'", None), []),
    ([9], ['await']),
]
assert_eq(len(cases), len(EXPECTED))
for i, (f, expected) in enumerate(zip(cases, EXPECTED)):
    assert_eq(run(f), expected, str(i))
async def co():
    return await aw(GenAwait())
def drive(c):
    try: c.send(None)
    except StopIteration as e: return e.value

def g():
    yield aw(GenAwait(8)).send(None)

assert_eq(run(lambda: drive(co())), ('done', ['await']))
assert_eq(run(lambda: list(g())), ([8], ['await']))

async def co(x):
    log.append('start')
    try:
        return await aw(x)
    finally:
        log.append('fin')
def steps(x, *ops):
    del log[:]
    c = co(x); out = []
    for op in ops:
        try:
            if op == 'close': out.append(c.close())
            elif op == 'throw': out.append(c.throw(KeyError('k')))
            else: out.append(c.send(op))
        except BaseException as e: out.append((type(e).__name__, str(e), getattr(e, 'value', None)))
    return out, log[:]
AWAITED = [
    (PlainAwait, (None, None)),
    (PlainAwait, (None, 5)),
    (PlainAwait, (None, 'throw')),
    (PlainAwait, (None, 'close')),
    (GenAwait, (None, 3, None)),
    (GenAwait, (None, 'throw')),
    (GenAwait, (None, 'close')),
    (StopAsync, (None,)),
    (BadAwait, (None,)),
    (RaiseAwait, (None,)),
    (ListAwait, (None, None, 'close')),
    (ListAwait, (None, 4)),
]
AWAITED_EXPECTED = [
    ([1, 1], ['start', 'await', ('next', 1), 'await', ('next', 1)]),
    ([1, 5], ['start', 'await', ('next', 1), 'await', ('send', 5)]),
    ([1, ('StopIteration', 'dflt', 'dflt')], ['start', 'await', ('next', 1), 'await', ('throw', 1), 'fin']),
    ([1, None], ['start', 'await', ('next', 1), 'await', 'close', 'fin']),
    ([1, ('TypeError', "can't send non-None value to a just-started generator", None), ('RuntimeError', 'cannot reuse already awaited coroutine', None)], ['start', 'await', 'fin']),
    ([1, ('KeyError', "'k'", None)], ['start', 'await', 'fin']),
    ([1, None], ['start', 'await', 'fin']),
    ([('StopIteration', 'dflt', 'dflt')], ['start', 'await', 'fin']),
    ([('TypeError', 'BadAwait.__await__() must return an iterator, not int', None)], ['start', 'fin']),
    ([('LookupError', 'aw', None)], ['start', 'fin']),
    ([1, 1, ('AttributeError', "'list_iterator' object has no attribute 'close'", None)], ['start', 'fin']),
    ([1, ('AttributeError', "'list_iterator' object has no attribute 'send'", None)], ['start', 'fin']),
]
for (x, ops), expected in zip(AWAITED, AWAITED_EXPECTED):
    args = (1, 2) if x is GenAwait else ()
    assert_eq(steps(x(*args), *ops), expected, x.__name__ + repr(ops))
