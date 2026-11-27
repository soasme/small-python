# Replays StarredOperands.tla: each case compiles a del statement or a
# parenthesized starred item and gives its SyntaxError's message.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

OPERANDS = {"name": "a", "lambda": "lambda: 0", "or": "a or b", "yield": "yield"}


def source(p):
    if p["part"] == "del":
        return "del " + {"name": "x", "call": "f()"}[p["before"]] + ", *" + OPERANDS[p["operand"]]
    return "(*" + OPERANDS[p["operand"]] + ")"


def outcome(p):
    try:
        compile(source(p) + "\n", "<starred>", "exec")
    except SyntaxError as e:
        return e.msg
    return "ok"


check_programs(outcome)
