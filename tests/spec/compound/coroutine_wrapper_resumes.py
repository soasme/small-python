# spec: PLS-315 27.4.2, 27.2.4, 27.4.1
# description: a coroutine wrapper's __next__ (also by next()), send,
# throw and close resume the coroutine as its own send, throw and close
# do, also when called as values with starred arguments; a coroutine that
# becomes unreachable while suspended in an await closes there, the
# awaited iterator's cleanup first, and one that ignores the GeneratorExit
# is left; inside functions as at module level.
from harness import *

log = []

class Ready:
    def __await__(self):
        try:
            got = yield "suspend"
        finally:
            for _ in range(2): pass
            log.append("ready done")
        return 10 if got is None else got * 10

async def uses():
    first = await Ready()
    second = await Ready()
    return first + second

async def catches():
    try:
        await Ready()
    except KeyError as e:
        return "caught " + e.args[0]

def call(f, *args):
    try:
        return f(*args)
    except StopIteration as e:
        return ("stop", e.value)

def wrappers():
    out = []
    w = uses().__await__()
    out.append([next(w), w.send(2), call(w.send, 3)])
    t = catches().__await__()
    out.append([call(next, t), call(t.throw, KeyError("k"))])
    c = catches()
    out.append([call(c.send, None), call(c.throw, KeyError("j"))])
    u = uses().__await__()
    next(u)
    out.append(u.close())
    out.append(log[:]); log.clear()
    return out

expected = [["suspend", "suspend", ("stop", 50)],
            ["suspend", ("stop", "caught k")],
            ["suspend", ("stop", "caught j")],
            None,
            ["ready done", "ready done", "ready done", "ready done", "ready done"]]
assert_eq(wrappers(), expected)
log.clear()
w = uses().__await__()
assert_eq([next(w), w.send(1), call(w.send, 1)], ["suspend", "suspend", ("stop", 20)])
log.clear()

# An unreachable coroutine suspended in an await closes there.
async def plain():
    try:
        await Ready()
    finally:
        log.append("plain finally")

async def stubborn():
    try:
        await Ready()
    finally:
        log.append("stubborn finally")
        raise ValueError("ignored")

def dropped():
    log.clear()
    c = plain(); c.send(None)
    del c
    log.append("after plain")
    s = stubborn(); s.send(None)
    s = None
    log.append("after stubborn")
    return log[:]

assert_eq(dropped(), ["ready done", "plain finally", "after plain", "ready done", "stubborn finally", "after stubborn"])
