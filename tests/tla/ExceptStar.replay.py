# Replays ExceptStar.tla: each case runs the spec's try statement with
# except* clauses and compares the clauses that ran, and what escaped, with
# the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

EXCEPTIONS = {
    "V": "ValueError()", "T": "TypeError()", "K": "KeyError()",
    "EG(V,T)": "ExceptionGroup('', [ValueError(), TypeError()])",
    "EG(V,EG(K))": "ExceptionGroup('', [ValueError(), ExceptionGroup('', [KeyError()])])",
    "EG(T,K)": "ExceptionGroup('', [TypeError(), KeyError()])",
}
LETTERS = {ValueError: "V", TypeError: "T", KeyError: "K", RuntimeError: "R"}


def leaves(e):
    if isinstance(e, BaseExceptionGroup):
        return "".join(sorted("".join(leaves(x) for x in e.exceptions)))
    return LETTERS[type(e)]


def outcome(p):
    raised, clauses = p
    lines = ["try:", "    raise " + EXCEPTIONS[raised]]
    for k, clause in enumerate(clauses, 1):
        lines.append("except* %s as eg:" % clause["type"])
        lines.append("    log.append((%d, leaves(eg)))" % k)
        lines.append({"pass": "    pass", "raise": "    raise", "new": "    raise RuntimeError()"}[clause["action"]])
    log = []
    try:
        exec("\n".join(lines) + "\n", {"log": log, "leaves": leaves})
    except Exception as e:
        return (tuple(log), "group" if isinstance(e, BaseExceptionGroup) else "single", leaves(e))
    return (tuple(log), "none", "")


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
