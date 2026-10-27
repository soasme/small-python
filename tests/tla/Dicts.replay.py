# Replays Dicts.tla: each case performs the spec's steps on one dict,
# comparing every result with the model's.
FIELDS = ("op", "result")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def perform(d, op):
    name, k, v = op
    try:
        if name == "set":
            d[k] = v
            return "None"
        if name == "del":
            del d[k]
            return "None"
        if name == "pop":
            return str(d.pop(k))
        if name == "popitem":
            key, value = d.popitem()
            return "%s=%d" % (key, value)
        if name == "setdefault":
            return str(d.setdefault(k, v))
        if name == "get":
            return str(d.get(k))
        if name == "in":
            return str(k in d)
        return ",".join("%s=%d" % item for item in list(d.items()))
    except KeyError:
        return "KeyError"


failures = 0
count = 0
for walk in walks():
    count += 1
    steps = states(walk)
    next(steps)
    d = {}
    recent = []
    for state in steps:
        actual = perform(d, state["op"])
        recent = (recent + [state["op"]])[-8:]
        if actual != state["result"]:
            failures += 1
            print("MISMATCH after", recent[:-1], "at", state["op"], "expected", state["result"], "got", actual)
            break
if failures:
    print(failures, "mismatches")
else:
    print("replayed", count, "cases")
