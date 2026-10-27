# Replays Tokens.tla: each case runs "r = <source>" with a = 2 and b = 1
# and compares r's type and repr, or the exception, with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def outcome(p):
    namespace = {"a": 2, "b": 1}
    try:
        exec(compile("r = " + "".join(p), "<program>", "exec"), namespace)
    except (SyntaxError, NameError, ValueError) as error:
        return (type(error).__name__, "")
    r = namespace["r"]
    return (type(r).__name__, repr(r))


check_programs(outcome)
