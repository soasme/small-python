# spec: PLS-315 27.2.4, 27.5.4
# description: A dead asynchronous generator or coroutine suspended in an
# await of a generator-based coroutine closes there: a live awaited one is
# closed first; one already closed (ended), as when a collection reclaims
# both and closes it first, is skipped, and GeneratorExit raises at the
# await, whose handler and finally run. A handler that yields or awaits
# ignores the GeneratorExit and the frame is cleared without its finally.
from harness import assert_eq, host

log = []


def coroutine(f):
    # The iterable-coroutine flag (27.4.5).
    f.__code__ = f.__code__.replace(co_flags=f.__code__.co_flags | 0x100)
    return f


@coroutine
def step():
    try:
        yield 1
    finally:
        log.append("inner")


class Pause:
    def __await__(self):
        return (yield "p")


def outcome(p):
    handler = p["handler"]

    async def agen(inner):
        try:
            try:
                await inner
            except GeneratorExit:
                # A loop puts the handler on the machine.
                for _ in (): pass
                log.append("exit")
                if handler == "yield": yield 2
                if handler == "raise": raise KeyError
        finally:
            log.append("done")
        yield 3

    async def coro(inner):
        try:
            try:
                await inner
            except GeneratorExit:
                for _ in (): pass
                log.append("exit")
                if handler == "yield": await Pause()
                if handler == "raise": raise KeyError
        finally:
            log.append("done")

    inner = step()
    g = (agen if p["kind"] == "asyncgen" else coro)(inner)
    (g.asend(None) if p["kind"] == "asyncgen" else g).send(None)
    if p["inner"] == "ended":
        inner.close()
    del inner, log[:]
    if p["death"] == "cycle":
        box = [g]
        box.append(box)
        del box
    del g
    host.collect()
    return " ".join(log)


# The reclaimed pair, its awaited one closed first (unordered in CPython's
# collector), and each other way it dies.
def pair(kind):
    inner = step()
    async def agen():
        try:
            await inner
        finally:
            log.append("done")
        yield 1
    async def coro():
        try:
            await inner
        finally:
            log.append("done")
    g = (agen if kind == "asyncgen" else coro)()
    (g.asend(None) if kind == "asyncgen" else g).send(None)
    box = [g, inner]
    box.append(box)
    del g, inner, box, log[:]
    host.collect()
    return sorted(log)
assert_eq(pair("asyncgen"), ["done", "inner"])
assert_eq(pair("coroutine"), ["done", "inner"])
assert_eq(outcome(dict(kind="asyncgen", inner="live", death="drop", handler="finish")), "inner exit done")
assert_eq(outcome(dict(kind="asyncgen", inner="live", death="drop", handler="raise")), "inner exit done")
assert_eq(outcome(dict(kind="asyncgen", inner="live", death="drop", handler="yield")), "inner exit")
assert_eq(outcome(dict(kind="asyncgen", inner="live", death="cycle", handler="finish")), "inner exit done")
assert_eq(outcome(dict(kind="asyncgen", inner="live", death="cycle", handler="raise")), "inner exit done")
assert_eq(outcome(dict(kind="asyncgen", inner="live", death="cycle", handler="yield")), "inner exit")
assert_eq(outcome(dict(kind="asyncgen", inner="ended", death="drop", handler="finish")), "exit done")
assert_eq(outcome(dict(kind="asyncgen", inner="ended", death="drop", handler="raise")), "exit done")
assert_eq(outcome(dict(kind="asyncgen", inner="ended", death="drop", handler="yield")), "exit")
assert_eq(outcome(dict(kind="asyncgen", inner="ended", death="cycle", handler="finish")), "exit done")
assert_eq(outcome(dict(kind="asyncgen", inner="ended", death="cycle", handler="raise")), "exit done")
assert_eq(outcome(dict(kind="asyncgen", inner="ended", death="cycle", handler="yield")), "exit")
assert_eq(outcome(dict(kind="coroutine", inner="live", death="drop", handler="finish")), "inner exit done")
assert_eq(outcome(dict(kind="coroutine", inner="live", death="drop", handler="raise")), "inner exit done")
assert_eq(outcome(dict(kind="coroutine", inner="live", death="drop", handler="yield")), "inner exit")
assert_eq(outcome(dict(kind="coroutine", inner="live", death="cycle", handler="finish")), "inner exit done")
assert_eq(outcome(dict(kind="coroutine", inner="live", death="cycle", handler="raise")), "inner exit done")
assert_eq(outcome(dict(kind="coroutine", inner="live", death="cycle", handler="yield")), "inner exit")
assert_eq(outcome(dict(kind="coroutine", inner="ended", death="drop", handler="finish")), "exit done")
assert_eq(outcome(dict(kind="coroutine", inner="ended", death="drop", handler="raise")), "exit done")
assert_eq(outcome(dict(kind="coroutine", inner="ended", death="drop", handler="yield")), "exit")
assert_eq(outcome(dict(kind="coroutine", inner="ended", death="cycle", handler="finish")), "exit done")
assert_eq(outcome(dict(kind="coroutine", inner="ended", death="cycle", handler="raise")), "exit done")
assert_eq(outcome(dict(kind="coroutine", inner="ended", death="cycle", handler="yield")), "exit")
