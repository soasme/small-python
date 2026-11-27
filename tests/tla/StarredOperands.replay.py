# Replays StarredOperands.tla: each case compiles a del statement, a
# parenthesized starred item or a comprehension, and gives its SyntaxError's
# message, or "ok".
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

OPERANDS = {"name": "a", "lambda": "lambda: 0", "or": "a or b", "yield": "yield"}


def source(p):
    if p["part"] == "del":
        return "del " + {"name": "x", "call": "f()"}[p["before"]] + ", *" + OPERANDS[p["operand"]]
    if p["part"] == "group":
        return "(*" + OPERANDS[p["operand"]] + ")"
    return ("(%s)" if p["display"] == "generator" else "[%s]") % "*a or b for x in y"


def outcome(p):
    try:
        compile(source(p) + "\n", "<starred>", "exec")
    except SyntaxError as e:
        return e.msg
    return "ok"


check_programs(outcome)
