# Replays Calls.tla: each case defines the spec's function, makes the call,
# and compares what each parameter was bound to with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def parameter(name, kind):
    return name if kind == "req" else f"{name}='d_{name}'"


def source(p):
    params = []
    if p["po"] != "none":
        params += [parameter("a", p["po"]), "/"]
    if p["pk"] != "none":
        params.append(parameter("b", p["pk"]))
    if p["star"]:
        params.append("*args")
    elif p["ko"] != "none":
        params.append("*")
    if p["ko"] != "none":
        params.append(parameter("c", p["ko"]))
    if p["kw"]:
        params.append("**kw")
    present = [name for name, kind in (("a", p["po"]), ("b", p["pk"]), ("c", p["ko"])) if kind != "none"]
    values = ", ".join(name if name in present else "'-'" for name in "abc")
    rest = ("args" if p["star"] else "()") + ", " + ("frozenset(kw.items())" if p["kw"] else "frozenset()")
    arguments = [f"'p{i}'" for i in range(1, p["npos"] + 1)] + [f"{k}='k_{k}'" for k in sorted(p["keys"])]
    return f"def f({', '.join(params)}):\n    return ({values}, {rest})\nresult = f({', '.join(arguments)})\n"


def outcome(p):
    try:
        code = compile(source(p), "<program>", "exec")
    except SyntaxError:
        return ("syntax", "-", "-", "-", (), frozenset())
    namespace = {}
    try:
        exec(code, namespace)
    except TypeError:
        return ("TypeError", "-", "-", "-", (), frozenset())
    return ("ok",) + namespace["result"]


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
