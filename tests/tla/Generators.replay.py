# Replays Generators.tla: each case starts a generator or coroutine running
# the spec's body and performs the spec's steps on it, comparing every
# result with the model's. Uses only the core language.
FIELDS = ("kind", "variant", "op", "result")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


K = 2


class Y:
    """An awaitable that suspends its coroutine once, yielding value."""
    def __init__(self, value):
        self.value = value

    def __await__(self):
        return (yield self.value)


def make(kind, variant):
    me = None

    def resume_self():
        if kind == "generator":
            next(me)
        else:
            me.send(None)

    def body():
        last, i = None, 0
        while i < K:
            try:
                got = yield (i, last)
            except ValueError:
                got = "caught"
            except GeneratorExit:
                if variant == "plain":
                    raise
                got = "exit"
                yield ("ignored", i)
            if got == "stop":
                return "early"
            if got == "reenter":
                try:
                    resume_self()
                except ValueError:
                    got = "blocked"
            last, i = got, i + 1
        return "done"

    async def coroutine():
        last, i = None, 0
        while i < K:
            try:
                got = await Y((i, last))
            except ValueError:
                got = "caught"
            except GeneratorExit:
                if variant == "plain":
                    raise
                got = "exit"
                await Y(("ignored", i))
            if got == "stop":
                return "early"
            if got == "reenter":
                try:
                    resume_self()
                except ValueError:
                    got = "blocked"
            last, i = got, i + 1
        return "done"

    me = body() if kind == "generator" else coroutine()
    return me


def text(value):
    return "None" if value is None else value


def perform(kind, target, op):
    try:
        if op[0] == "send":
            if op[1] == "None" and kind == "generator":
                value = next(target)
            else:
                value = target.send(None if op[1] == "None" else op[1])
        elif op[0] == "throw":
            value = target.throw({"ValueError": ValueError, "KeyError": KeyError}[op[1]])
        else:
            return ("return", text(target.close()))
        return ("yield", value[0], text(value[1]))
    except StopIteration as stop:
        return ("stop", text(stop.value))
    except (ValueError, KeyError, TypeError, RuntimeError) as error:
        return ("raise", type(error).__name__)


failures = 0
count = 0
for walk in walks():
    count += 1
    steps = states(walk)
    start = next(steps)
    target = make(start["kind"], start["variant"])
    recent = []
    for state in steps:
        actual = perform(start["kind"], target, state["op"])
        recent = (recent + [state["op"]])[-8:]
        if actual != state["result"]:
            failures += 1
            print("MISMATCH", start["kind"], start["variant"], "after", recent[:-1], "at", state["op"],
                  "expected", state["result"], "got", actual)
            break
    # Two close() calls finish any object (the spec's CloseTwice), so none is
    # left to be finalized while suspended.
    for attempt in range(2):
        try:
            target.close()
            break
        except RuntimeError:
            pass
if failures:
    print(failures, "mismatches")
else:
    print("replayed", count, "cases")
