# Replays Super.tla: each case defines the spec's diamond, calls m or
# __get__ on an instance, and compares the log with the model's.
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
        elif p["name"] == "p":
            lines.append("    @property")
            lines.append("    def p(self):")
            lines.append("        for _ in (): pass")
            lines.append("        log.append(%r)" % c)
            if kind == "super":
                lines.append("        return super().p")
        else:
            lines.append("    def %s(self, *args):" % p["name"])
            lines.append("        log.append(%r)" % c)
            if kind == "super":
                lines.append("        super().%s(%s)" % (p["name"], "self" if p["name"] == "__get__" else ""))
    if p["name"] == "p":
        lines.append("%s().p" % p["call"])
    else:
        lines.append("%s().%s(%s)" % (p["call"], p["name"], "None" if p["name"] == "__get__" else ""))
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
