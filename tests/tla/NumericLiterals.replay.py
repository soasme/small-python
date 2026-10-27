# Replays NumericLiterals.tla: each case evaluates the spec's string as an
# expression and compares the outcome with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def outcome(p):
    try:
        code = compile("".join(p), "<literal>", "eval")
    except SyntaxError:
        return ("SyntaxError", "")
    try:
        return ("value", repr(eval(code, {"__builtins__": {}})))
    except (NameError, AttributeError) as error:
        return (type(error).__name__, "")


check_programs(outcome)
