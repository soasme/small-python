# Replays IntArith.tla: each case evaluates the spec's expression and
# compares its value or exception with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def evaluate(p):
    if p["kind"] == "unary":
        source = f"abs({p['a']})" if p["op"] == "abs" else f"{p['op']}({p['a']})"
    elif p["op"] == "divmod":
        source = f"divmod({p['a']}, {p['b']})"
    else:
        source = f"({p['a']}) {p['op']} ({p['b']})"
    try:
        value = eval(source)
    except (ZeroDivisionError, ValueError) as error:
        return ("raise", 0, 0, type(error).__name__)
    if type(value) is tuple:
        return ("pair", value[0], value[1], "")
    if type(value) is float:
        return ("float", 0, 0, "")
    return ("int", value, 0, "")


failures = 0
count = 0
for walk in walks():
    count += 1
    steps = states(walk)
    program = next(steps)["program"]
    for state in steps:
        actual = evaluate(program)
        if actual != state["outcome"]:
            failures += 1
            if failures <= 20:
                print("MISMATCH", program, "expected", state["outcome"], "got", actual)
if failures:
    print(failures, "mismatches")
else:
    print("replayed", count, "cases")
