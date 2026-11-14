# Replays StubbornReclaim.tla: each case drops the spec's number of
# stubborn generators or coroutines one after another and compares the log
# with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

log = []


class Held:
    def __del__(self):
        log.append("del")


def inner():
    try:
        yield "inner"
    finally:
        log.append("inner")


class Waiting:
    def __await__(self):
        return (yield from inner())


class Once:
    def __await__(self):
        yield "once"


def generator(delegates):
    held = Held()
    try:
        yield 1
    except GeneratorExit:
        log.append("ignored")
        if delegates:
            yield from inner()
        else:
            yield 2


async def coroutine(delegates):
    held = Held()
    try:
        await Once()
    except GeneratorExit:
        log.append("ignored")
        await (Waiting() if delegates else Once())


def round(kind, delegates):
    target = generator(delegates) if kind == "generator" else coroutine(delegates)
    target.send(None)
    del target
    log.append("dropped")


def outcome(p):
    del log[:]
    for _ in range(p["rounds"]):
        round(p["kind"], p["delegates"])
    return tuple(log)


check_programs(outcome)
