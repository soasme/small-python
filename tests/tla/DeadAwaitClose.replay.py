# Replays DeadAwaitClose.tla: each case suspends the program's async
# generator or coroutine in an await of a generator-based coroutine,
# closes that one first when it ended, lets the other die, collects (or
# allocates until the engine collects), and writes the log its close left.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

from harness import host

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
    if p["death"] != "drop":
        box = [g]
        box.append(box)
        del box
    del g
    if p["death"] == "automatic":
        # Allocate cycles until a collection the engine starts reclaims it.
        n = 0
        while not log and n < 2000000:
            junk = [[]]
            junk.append(junk)
            n += 1
    else:
        host.collect()
    return " ".join(log)


check_programs(outcome)
