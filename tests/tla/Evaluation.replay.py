# Replays Evaluation.tla: each case runs the spec's form with logging
# operands and compares the log and the value with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SOURCES = {
    "and": "result = t(1) and t(2)",
    "or": "result = t(1) or t(2)",
    "chain": "result = t(1) < t(2) < t(3)",
    "cond": "result = t(2) if t(1) else t(3)",
    "arith": "result = t(1) - t(2) * t(3)",
    "call": "c.f(t(1), k=t(2), *[t(3)])",
    "dict": "{t(1): t(2), t(3): 0}",
    "dictcomp": "{t(1): t(2) for _ in [0]}",
    "assign": "c[t(1)] = t(2)",
    "multi": "c[t(1)] = c[t(2)] = t(3)",
    "augment": "c[t(1)] += t(2)",
    "unpack": "c[t(1)], c[t(2)] = t(3), t(3)",
}


class Container:
    def __init__(self, log):
        self.log = log

    def __getitem__(self, key):
        self.log.append("get")
        return 0

    def __setitem__(self, key, value):
        self.log.append("set")

    def __getattr__(self, name):
        self.log.append("attr")

        def f(*args, **kwargs):
            self.log.append("call")
        return f


def outcome(p):
    log = []
    values = p["v"]

    def t(k):
        log.append("t%d" % k)
        return values[k - 1]

    namespace = {"t": t, "c": Container(log), "result": "-"}
    exec(SOURCES[p["form"]], namespace)
    return (tuple(log), str(namespace["result"]))


failures = 0
count = 0
for walk in walks():
    count += 1
    steps = states(walk)
    program = next(steps)["program"]
    for state in steps:
        actual = outcome(program)
        if actual != state["outcome"]:
            failures += 1
            if failures <= 20:
                print("MISMATCH", program, "expected", state["outcome"], "got", actual)
if failures:
    print(failures, "mismatches")
else:
    print("replayed", count, "cases")
