# Replays WithStarTargets.tla: each case compiles  with a as *<operand>: pass
# and gives its SyntaxError's message, column and end column.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def outcome(operand):
    try:
        compile("with a as *" + operand + ": pass\n", "<with>", "exec")
    except SyntaxError as e:
        if e.msg == "starred assignment target must be in a list or tuple":
            return (e.msg, 0, 0)
        return (e.msg, e.offset, e.end_offset)
    return ("ok", 0, 0)


check_programs(outcome)
