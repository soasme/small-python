# Replays Iteration.tla: each case runs the spec's for statement over an
# object with the spec's protocol and compares the log with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def make(protocol, n):
    namespace = {}
    if protocol == "iter":
        class Iterator:
            def __init__(self):
                self.i = 0

            def __next__(self):
                if self.i >= n:
                    raise StopIteration
                self.i += 1
                return self.i - 1
        namespace["__iter__"] = lambda self: Iterator()
    elif protocol == "bad":
        namespace["__iter__"] = lambda self: 1
    if protocol in ("getitem", "blocked"):
        def getitem(self, i):
            if i >= n:
                raise IndexError(i)
            return i
        namespace["__getitem__"] = getitem
    if protocol == "blocked":
        namespace["__iter__"] = None
    return type("S", (), namespace)()


def outcome(p):
    log = []
    try:
        for x in make(p["protocol"], p["n"]):
            if x == p["brk"]:
                log.append("break")
                break
            if x == p["skip"]:
                log.append("skip")
                continue
            log.append(str(x))
        else:
            log.append("else")
    except TypeError:
        return (tuple(log), "TypeError")
    return (tuple(log), "ok")


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
