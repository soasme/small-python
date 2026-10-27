# Replays StringLiterals.tla: each case evaluates the spec's literal, in
# parentheses, and compares its type and code points with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def outcome(p):
    quote = "'''" if p["triple"] else "'"
    source = "(" + p["prefix"] + quote + "".join(p["body"]) + quote + ")"
    try:
        value = eval(compile(source, "<literal>", "eval"), {"__builtins__": {}})
    except SyntaxError:
        return ("SyntaxError", ())
    if type(value) is bytes:
        return ("bytes", tuple(value))
    return ("str", tuple(ord(c) for c in value))


check_programs(outcome)
