# Replays ForTargets.tla: each case compiles the target in a for statement
# or a list comprehension and gives its SyntaxError's message.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

TARGETS = {"lambda": "lambda: 0", "conditional": "a if b else c", "call": "f()", "comparison": "a < b", "name and lambda": "a, lambda: 0"}


def outcome(p):
    target = TARGETS[p["target"]]
    source = "for " + target + " in x: pass\n" if p["place"] == "statement" else "[0 for " + target + " in x]\n"
    try:
        compile(source, "<for>", "exec")
    except SyntaxError as e:
        return e.msg
    return "ok"


check_programs(outcome)
