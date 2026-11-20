# Replays BasesAssignment.tla: each case builds the spec's classes, stores
# C.__bases__ as the program says, and compares the outcome with the
# model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def outcome(p):
    log = []
    fail = p["fail"]

    class M(type):
        def mro(cls):
            for _ in (): pass
            log.append(cls.__name__)
            if cls.__name__ == fail and getattr(cls, "armed", False):
                raise LookupError("mro")
            return type.mro(cls)

    class A: pass
    class B: pass
    C = M("C", (A,), {})
    D = M("D", (C,), {})
    E = M("E", (D,), {})
    for cls in (C, D, E):
        cls.armed = True
    del log[:]
    bases = ({"A": A, "B": B}[p["target"]],)
    kind = "ok"
    try:
        if p["store"] == "assign":
            C.__bases__ = bases
        elif p["store"] == "for":
            for C.__bases__ in [bases]:
                pass
        else:
            setattr(C, "__bases__", bases)
    except LookupError:
        kind = "LookupError"
    names = lambda t: tuple(k.__name__ for k in t)
    return (kind, names(C.__bases__), names(D.__mro__), names(E.__mro__), tuple(log))


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
