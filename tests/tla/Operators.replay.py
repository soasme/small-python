# Replays Operators.tla: each case defines the spec's classes, or
# metaclasses for holder "class", applies the operator to their instances,
# and compares which method answered with the model's.
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
    meta = p["holder"] == "class"
    base = p["holder"] if p["holder"] in ("int", "str") else None
    source = ("class L(type):\n" if meta else f"class L({base}):\n" if base else "class L:\n") + body("L", p["L"]) + "\n"
    if p["rel"] in ("same", "exact"):
        source += "R = L\n"
    else:
        source += ("class R(L):\n" if p["rel"] == "sub" else "class R(type):\n" if meta else f"class R({base}):\n" if base else
                   "class R:\n") + body("R", p["R"]) + "\n"
    made = "('X', (), {})" if meta else "()"
    left, right = ("(1)", "(2)") if base == "int" else ("('a')", "('b')") if base else (made, made)
    source += f"x = L{left}; x.name = 'x'\n"
    source += (f"y = {base}{right}\n" if p["rel"] == "exact" else f"y = R{right}; y.name = 'y'\n")
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
