# spec: PLS-315 9.7, 27.2.4
# description: A collection that the engine starts on its own, while a
# program allocates, finalizes the cycles it reclaims as an explicit one
# does: an instance's __del__, a generator's finally and a coroutine's
# GeneratorExit handler at an await of a generator-based coroutine all run,
# each of which may loop and make calls, and the program goes on after them.
from harness import assert_eq
log = []
def note(entry):
    for _ in range(2): pass
    log.append(entry)
def coroutine(f):
    # The iterable-coroutine flag (27.4.5).
    f.__code__ = f.__code__.replace(co_flags=f.__code__.co_flags | 0x100)
    return f
@coroutine
def step():
    yield 1
async def coro(box):
    try:
        await step()
    except GeneratorExit:
        note("exit")
        raise
    finally:
        note("coro done")
def gen(box):
    try:
        yield
    finally:
        note("gen done")
class Del:
    def __del__(self): note("del")
def make():
    box = []
    c = coro(box); box.append(c); c.send(None)
    g = gen(box); box.append(g); next(g)
    d = Del(); d.me = d; box.append(d)
def run():
    del log[:]
    make()
    n = 0
    while len(log) < 4 and n < 2000000:
        junk = [[]]; junk.append(junk); n += 1
    log.append("after")
    return sorted(log[:-1]), log[-1]
expected = (["coro done", "del", "exit", "gen done"], "after")
assert_eq(run(), expected)
def outer(): yield run()
assert_eq(next(outer()), expected)
