# Replays StarredOperands.tla: each case compiles a del statement, a
# parenthesized starred item, a comprehension or a starred not, and gives
# its SyntaxError's message, or "ok".
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

OPERANDS = {"name": "a", "lambda": "lambda: 0", "or": "a or b", "yield": "yield"}


def source(p):
    if p["part"] == "del":
        return "del " + {"name": "x", "call": "f()"}[p["before"]] + ", *" + OPERANDS[p["operand"]]
    if p["part"] == "group":
        return "(*" + OPERANDS[p["operand"]] + ")"
    if p["part"] == "element":
        return ("(%s)" if p["display"] == "generator" else "[%s]") % "*a or b for x in y"
    return {"list": "[*not a]", "call": "f(*not a)", "subscript": "x[*not a]", "comparison": "a < not b", "sum": "a + not b"}[p["place"]]


def outcome(p):
    try:
        compile(source(p) + "\n", "<starred>", "exec")
    except SyntaxError as e:
        return e.msg
    return "ok"


check_programs(outcome)
