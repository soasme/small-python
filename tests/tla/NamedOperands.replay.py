# Replays NamedOperands.tla: each case compiles a statement and gives its
# SyntaxError's message and column.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SOURCES = {"cond": "a b if c", "chain": "a b c if d", "not": "a not b if c", "assigned": "x = a b if c",
           "comma": "a, b c if d", "attribute": "a.b c if d", "number": "1 b if c", "call": "x f(*)",
           "colon": "a b if c:", "bracketed": "(a b if c)"}


def outcome(program):
    try:
        compile(SOURCES[program], "<named>", "exec")
    except SyntaxError as e:
        return (e.msg, e.offset)
    return ("ok", 0)


check_programs(outcome)
