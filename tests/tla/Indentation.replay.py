# Replays Indentation.tla: each case runs the spec's lines and compares the
# log, or the class of the error, with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

TEXT = {"t": "if 1:", "f": "if 0:", "b": ""}


def outcome(p):
    lines = [indent + TEXT.get(kind, f"log.append({i})") for i, (indent, kind) in enumerate(p, 1)]
    try:
        code = compile("\n".join(lines) + "\n", "<program>", "exec")
    except SyntaxError as error:
        return (type(error).__name__, ())
    log = []
    exec(code, {"log": log})
    return ("ok", tuple(log))


check_programs(outcome)
