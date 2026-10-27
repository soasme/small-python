# Replays GC.tla: each case performs the spec's steps on real objects held
# by the globals x, y, and saved, and compares the __del__ calls each step
# makes with the model's. Automatic collection is disabled so that only the
# spec's Collect steps collect cycles.
import gc

FIELDS = ("op", "out")
CASES = ""  # filled in by tests/tla_check.py


def walks():
    """The walks, one at a time: CASES holds them all, a blank line apart."""
    start = 0
    while start < len(CASES):
        end = CASES.find("\n\n", start)
        end = len(CASES) if end < 0 else end
        yield CASES[start:end]
        start = end + 2


def states(walk):
    """The states of a walk, decoded one line at a time."""
    start = 0
    while start < len(walk):
        end = walk.find("\n", start)
        end = len(walk) if end < 0 else end
        yield eval(walk[start:end])
        start = end + 1

gc.disable()
log = []
x = y = saved = None


class A:
    def __init__(self, name):
        self.name = name
        self.ref = None
        self.other = None

    def __del__(self):
        log.append(self.name)


class Phoenix(A):
    def __del__(self):
        global saved
        log.append(self.name)
        saved = self


SOURCE = {
    "new": lambda v, o: f"{v} = {'Phoenix' if o == 'p' else 'A'}({o!r})",
    "link": lambda v, f, w: f"{v}.{f} = {w}",
    "load": lambda v, w, f: f"{v} = {w}.{f}",
    "del": lambda v: f"{v} = None",
    "collect": lambda: "gc.collect()",
}
CODE = {}


def perform(step):
    # Each step is one statement of its own, compiled once, so the harness
    # holds no reference to the objects while it runs.
    if step not in CODE:
        CODE[step] = compile(SOURCE[step[0]](*step[1:]), "<step>", "exec")
    del log[:]
    exec(CODE[step], globals())
    return tuple(sorted(log)) if step[0] == "collect" else tuple(log)


failures = 0
count = 0
for walk in walks():
    count += 1
    steps = states(walk)
    next(steps)
    recent = []
    for state in steps:
        actual = perform(state["op"])
        recent = (recent + [state["op"]])[-8:]
        if actual != state["out"]:
            failures += 1
            print("MISMATCH after", recent[:-1], "at", state["op"], "expected", state["out"], "got", actual)
            break
    x = y = saved = None
    gc.collect()
if failures:
    print(failures, "mismatches")
else:
    print("replayed", count, "cases")
