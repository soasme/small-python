# Replays OperationThrow.tla: each case suspends a coroutine in an await of
# anext(g), g suspended in an await of its own, throws the program's
# exception into the coroutine or closes it, and writes what that did.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


class Pause:
    def __await__(self):
        return (yield "p")


def outcome(p):
    caught = []

    async def body():
        try:
            await Pause()
        except (KeyError, GeneratorExit):
            # A loop puts the handler on the machine, as a pausing throw runs it.
            for _ in (): pass
            caught.append(True)
            if p["after"] == "yield":
                yield "handled"
            elif p["after"] == "await":
                yield await Pause()
            elif p["after"] == "return":
                return
        yield "end"

    async def driver(g):
        return await anext(g)

    co = driver(body())
    co.send(None)
    thrown = {"instance": KeyError("k"), "class": KeyError, "other": ValueError("v"), "close": None}[p["thrown"]]
    try:
        if thrown is None:
            co.close()
            result = "closed"
        else:
            co.throw(thrown)
            result = "suspended"
    except StopIteration as e:
        result = "value " + e.value
    except (StopAsyncIteration, ValueError, RuntimeError) as e:
        result = "raised " + type(e).__name__
    return "%s caught=%s" % (result, bool(caught))

check_programs(outcome)
