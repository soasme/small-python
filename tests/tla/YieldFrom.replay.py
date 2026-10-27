# Replays YieldFrom.tla: each case starts the spec's delegating generator
# and performs the spec's steps on it, comparing every result, and whether
# the subgenerator has finalized, with the model's.
FIELDS = ("op", "result", "finalized")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def make(log):
    def inner():
        last, i = "None", 0
        try:
            while i < 2:
                try:
                    got = yield ("in", str(i), last)
                except ValueError:
                    got = "caught"
                if got == "stop":
                    return "early"
                last, i = str(got), i + 1
            return "done"
        finally:
            log.append("inner")

    def outer():
        try:
            r = yield from inner()
        except KeyError:
            r = "keyerror"
        yield ("after", r, "-")
        return "end"
    return outer()


def perform(target, op):
    try:
        if op[0] == "send":
            value = next(target) if op[1] == "None" else target.send(op[1])
        elif op[0] == "throw":
            value = target.throw({"ValueError": ValueError, "KeyError": KeyError}[op[1]])
        else:
            return ("return", str(target.close()), "-", "-")
        return ("yield",) + value
    except StopIteration as stop:
        return ("stop", str(stop.value), "-", "-")
    except (ValueError, KeyError, TypeError) as error:
        return ("raise", type(error).__name__, "-", "-")


failures = 0
count = 0
for walk in walks():
    count += 1
    steps = states(walk)
    next(steps)
    log = []
    target = make(log)
    recent = []
    for state in steps:
        actual = (perform(target, state["op"]), bool(log))
        recent = (recent + [state["op"]])[-8:]
        if actual != (state["result"], state["finalized"]):
            failures += 1
            print("MISMATCH after", recent[:-1], "at", state["op"],
                  "expected", (state["result"], state["finalized"]), "got", actual)
            break
    target.close()
if failures:
    print(failures, "mismatches")
else:
    print("replayed", count, "cases")
