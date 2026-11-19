# Replays OperationClose.tla: each case makes the program's awaitable, begun
# when the program says so, suspending its async generator in an await,
# closes it or throws KeyError into it, and writes what the call did.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


class Pause:
    def __await__(self):
        return (yield "p")


def outcome(p):
    async def body():
        try:
            yield 1
        except (ValueError, GeneratorExit):
            pass
        try:
            await Pause()
        except (GeneratorExit, KeyError):
            # A loop puts the handler on the machine, as a pausing call runs it.
            for _ in (): pass
            if p["after"] == "yield":
                yield "kept"
            elif p["after"] == "await":
                await Pause()
            elif p["after"] == "raise":
                raise LookupError
            return

    g = body()
    try:
        g.asend(None).send(None)
    except StopIteration:
        pass
    a = {"asend": lambda: g.asend(None), "athrow": lambda: g.athrow(ValueError), "aclose": g.aclose}[p["kind"]]()
    if p["begun"]:
        a.send(None)
    try:
        result = a.close() if p["how"] == "close" else a.throw(KeyError)
        return "None" if result is None else "suspended"
    except (StopIteration, StopAsyncIteration, RuntimeError, LookupError, KeyError) as e:
        return type(e).__name__

check_programs(outcome)
