# Replays MatchErrors.tla: each case compiles the spec's match statement
# and compares the SyntaxError's message, column and end column with the
# model's, or "ok" when it compiles.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def outcome(pattern):
    try:
        compile("match x:\n    case %s: pass" % pattern, "<case>", "exec")
    except SyntaxError as e:
        return (e.msg, e.offset, e.end_offset)
    return ("ok", 0, 0)


check_programs(outcome)
