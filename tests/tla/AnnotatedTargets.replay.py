# Replays AnnotatedTargets.tla: each case compiles  <target>: int  or
# <target>:  and gives its SyntaxError's message, column and end column.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def outcome(p):
    try:
        compile(p["target"] + (": int\n" if p["annotation"] == "int" else ":\n"), "<annotated>", "exec")
    except SyntaxError as e:
        return (e.msg, e.offset, e.end_offset)
    return ("ok", 0, 0)


check_programs(outcome)
