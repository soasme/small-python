# Replays MRO.tla: each case runs the spec's class statements and compares
# each class's __mro__ with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def outcome(p):
    lines = ["class A: pass"]
    for c in "BCD":
        lines.append("class %s(%s): pass" % (c, ", ".join("object" if b == "O" else b for b in p[c])))
    namespace = {}
    kind = "ok"
    try:
        exec("\n".join(lines), namespace)
    except TypeError:
        kind = "TypeError"
    mros = []
    for c in "ABCD":
        if c not in namespace:
            break
        mros.append(tuple("O" if k is object else k.__name__ for k in namespace[c].__mro__))
    return (kind, tuple(mros))


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
