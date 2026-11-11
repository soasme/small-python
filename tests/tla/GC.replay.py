# Replays GC.tla (and GCGenerators.tla): each case performs the spec's steps
# on real objects held by the globals x, y, and saved, and compares the
# __del__ and close calls each step makes, and which objects a weak
# reference still reaches, with the model's. Automatic collection is
# disabled so that only the spec's Collect steps collect cycles.
from harness import host

FIELDS = ("op", "out", "alive")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


host.disable_automatic_collection()
log = []
weak = {}  # each object's weak reference, by name; frames have none
x = y = saved = None


class A:
    def __init__(self, name):
        self.name = name
        weak[name] = host.weak_reference(self)
        self.ref = None
        self.other = None

    def __del__(self):
        log.append(self.name)


class Phoenix(A):
    def __del__(self):
        global saved
        log.append(self.name)
        saved = self


def suspended():
    try:
        yield
    finally:
        log.append("g")


def started():
    g = suspended()
    next(g)
    weak["g"] = host.weak_reference(g)
    return g


SOURCE = {
    "new": lambda v, o: f"{v} = started()" if o == "g" else f"{v} = {'Phoenix' if o == 'p' else 'A'}({o!r})",
    "link": lambda v, f, w: f"{v}.{f} = {w}",
    "load": lambda v, w, f: f"{v} = {w}.{f}",
    "frame": lambda v, w: f"{v} = {w}.gi_frame",
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
    out = tuple(sorted(log)) if step[0] == "collect" else tuple(log)
    return out, frozenset(name for name, ref in weak.items() if ref() is not None)


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
        if actual != (state["out"], state["alive"] - {"f"}):
            failures += 1
            print("MISMATCH after", recent[:-1], "at", state["op"], "expected", (state["out"], state["alive"]), "got", actual)
            break
    x = y = saved = None
    host.collect()
    weak.clear()
if failures:
    print(failures, "mismatches")
else:
    print("replayed", count, "cases")
