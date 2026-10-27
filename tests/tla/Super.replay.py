# Replays Super.tla: each case defines the spec's diamond, calls m on an
# instance, and compares the log with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

BASES = {"A": "", "B": "(A)", "C": "(A)", "D": "(B, C)"}


def outcome(p):
    lines = []
    for c in "ABCD":
        lines.append("class %s%s:" % (c, BASES[c]))
        kind = p["kind"][c]
        if kind == "none":
            lines.append("    pass")
        else:
            lines.append("    def m(self):")
            lines.append("        log.append(%r)" % c)
            if kind == "super":
                lines.append("        super().m()")
    lines.append("%s().m()" % p["call"])
    log = []
    try:
        exec("\n".join(lines) + "\n", {"log": log})
    except AttributeError:
        return (tuple(log), "AttributeError")
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
