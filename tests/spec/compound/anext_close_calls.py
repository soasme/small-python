# spec: PLS-315 19.3.4, 27.5.1, 13.16.3
# description: close() of a coroutine suspended in an await of anext()
# of an async generator throws GeneratorExit into the generator through
# the asend: a handler's yield or return ends the close with None, an
# await raises RuntimeError and leaves the generator running, and an
# exception raised there is the close's; cr_await is then None.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Pause:
    def __await__(self):
        got = yield 'pause'
        return got
def spin():
    for _ in (): pass
async def values(mode):
    try:
        yield await Pause()
    except GeneratorExit:
        spin(); log.append(('exit', mode))
        if mode == 'yield': yield 'late'
        if mode == 'await': await Pause()
        if mode == 'raise': raise ValueError('v')
        if mode == 'stop': raise StopAsyncIteration
        if mode == 'return': return
        raise
    finally:
        log.append(('finally', mode))
for mode in ('plain', 'yield', 'await', 'raise', 'stop', 'return'):
    h = values(mode)
    async def two(): return await anext(h, 'default')
    c = two(); c.send(None)
    try:
        r = ('closed', c.close())
    except BaseException as e:
        r = (type(e).__name__, str(e))
    log.append((mode, r, h.ag_running, h.ag_frame is None, c.cr_await))
    try:
        r = h.asend(None).send(None)
    except BaseException as e:
        r = (type(e).__name__, str(e))
    log.append(('after', r))
for x in log: emit(x)
EXPECTED = [
    "('exit', 'plain')",
    "('finally', 'plain')",
    "('plain', ('closed', None), False, True, None)",
    "('after', ('StopAsyncIteration', ''))",
    "('exit', 'yield')",
    "('yield', ('closed', None), False, False, None)",
    "('finally', 'yield')",
    "('after', ('GeneratorExit', ''))",
    "('exit', 'await')",
    "('await', ('RuntimeError', 'coroutine ignored GeneratorExit'), True, False, None)",
    "('after', ('RuntimeError', 'anext(): asynchronous generator is already running'))",
    "('finally', 'await')",
    "('exit', 'raise')",
    "('finally', 'raise')",
    "('raise', ('ValueError', 'v'), False, True, None)",
    "('after', ('StopAsyncIteration', ''))",
    "('exit', 'stop')",
    "('finally', 'stop')",
    "('stop', ('RuntimeError', 'async generator raised StopAsyncIteration'), False, True, None)",
    "('after', ('StopAsyncIteration', ''))",
    "('exit', 'return')",
    "('finally', 'return')",
    "('return', ('closed', None), False, True, None)",
    "('after', ('StopAsyncIteration', ''))",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
