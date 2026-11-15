# Replays AsyncGenerators.tla: each case starts an async generator running
# the spec's body and performs the spec's steps on it, running each
# awaitable to completion, an asend() through an await or, in every other
# walk, sent to directly, a throw() into an asend() awaitable directly, and
# comparing its result with the model's.
FIELDS = ("variant", "op", "result")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

K = 2


def make(variant):
    async def body():
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
                return
            last, i = got, i + 1
    return body()


async def awaiting(awaitable):
    return await awaitable


def perform(target, op, direct):
    if op[0] == "asend":
        # Awaited, as an async for or await runs it, resuming the body there.
        awaitable = target.asend(None if op[1] == "None" else op[1])
        if not direct:
            awaitable = awaiting(awaitable)
    elif op[0] in ("athrow", "thrown"):
        error = {"ValueError": ValueError, "KeyError": KeyError}[op[1]]
        awaitable = target.athrow(error) if op[0] == "athrow" else target.asend(None)
    else:
        awaitable = target.aclose()
    try:
        if op[0] == "thrown":
            # Thrown into the asend() awaitable, which throws it into the body.
            awaitable.throw(error)
        else:
            awaitable.send(None)
        return ("suspended",)
    except StopIteration as stop:
        value = stop.value
        if value is None:
            return ("return", "None")
        return ("yield", value[0], "None" if value[1] is None else value[1])
    except (ValueError, KeyError, TypeError, RuntimeError, StopAsyncIteration) as error:
        return ("raise", type(error).__name__)


failures = 0
count = 0
for walk in walks():
    count += 1
    steps = states(walk)
    start = next(steps)
    target = make(start["variant"])
    recent = []
    for state in steps:
        actual = perform(target, state["op"], count % 2)
        recent = (recent + [state["op"]])[-8:]
        if actual != state["result"]:
            failures += 1
            print("MISMATCH", start["variant"], "after", recent[:-1], "at", state["op"],
                  "expected", state["result"], "got", actual)
            break
    # Run what is left of the body, so none is left to be finalized while
    # suspended (once closed, aclose() would not run it).
    for attempt in range(2 * K + 2):
        try:
            target.asend(None).send(None)
        except StopIteration:
            pass
        except StopAsyncIteration:
            break
if failures:
    print(failures, "mismatches")
else:
    print("replayed", count, "cases")
