# Replays GC.tla: each case performs the spec's steps on real objects held
# by the globals x, y, and saved, and compares the __del__ calls each step
# makes with the model's. Automatic collection is disabled so that only the
# spec's Collect steps collect cycles.
from harness import host

FIELDS = ("op", "out")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


host.disable_automatic_collection()
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
    "collect": lambda: "host.collect()",
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
    host.collect()
if failures:
    print(failures, "mismatches")
else:
    print("replayed", count, "cases")
