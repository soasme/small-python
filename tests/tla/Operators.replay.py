# Replays Operators.tla: each case defines the spec's classes, applies the
# operator, and compares which method answered with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def body(cls, methods):
    lines = []
    for m, kind in sorted(methods.items()):
        if kind == "value":
            lines.append(f"    def __{m}__(self, other): return '{cls}.{m}:' + self.name")
        elif kind == "NI":
            lines.append(f"    def __{m}__(self, other): return NotImplemented")
    return "\n".join(lines) or "    pass"


def outcome(p):
    source = "class L:\n" + body("L", p["L"]) + "\n"
    if p["rel"] == "same":
        source += "R = L\n"
    else:
        source += ("class R(L):\n" if p["rel"] == "sub" else "class R:\n") + body("R", p["R"]) + "\n"
    source += "x = L(); x.name = 'x'\ny = R(); y.name = 'y'\n"
    source += "x += y\nresult = x\n" if p["op"] == "+=" else f"result = x {p['op']} y\n"
    namespace = {}
    try:
        exec(source, namespace)
    except TypeError:
        return "TypeError"
    return str(namespace["result"])


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
