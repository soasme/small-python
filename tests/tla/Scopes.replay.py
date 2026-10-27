# Replays Scopes.tla: each case writes out the spec's program as Python
# source, compiles and runs it, and compares the outcome with the model's.
# Uses only the core language.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def source(p):
    lines = ["x = 'global'", "def outer():"]
    if p["odecl"] == "global":
        lines.append("    global x")
    if p["oassign"]:
        lines.append("    x = 'outer'")
    indent = "    "
    if p["cls"]:
        lines += ["    class C:", "        seen = x", "        x = 'class'"]
        indent = "        "
    lines.append(indent + "def inner():")
    if p["idecl"] != "none":
        lines.append(indent + f"    {p['idecl']} x")
    if p["before"]:
        lines.append(indent + "    x = 'inner'")
    lines.append(indent + ("    r = x" if p["read"] == "direct" else "    r = [x for _ in (1,)][0]"))
    if p["after"]:
        lines.append(indent + "    x = 'inner'")
    lines.append(indent + "    return r")
    if p["late"]:
        lines.append("    x = 'late'")
    if p["cls"]:
        lines.append("    return C.inner(), x, C.seen")
    else:
        lines.append("    return inner(), x, ''")
    lines.append("result = outer(), x")
    return "\n".join(lines) + "\n"


def outcome(p):
    try:
        code = compile(source(p), "<program>", "exec")
    except SyntaxError:
        return ("syntax", "", "", "", "")
    namespace = {}
    try:
        exec(code, namespace)
    except Exception as error:
        return ("raise", type(error).__name__, "", "", "")
    (read, view, seen), final = namespace["result"]
    return ("ok", read, view, final, seen)


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
