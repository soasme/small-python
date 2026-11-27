# Replays AssignmentMeant.tla: each case compiles an assignment whose
# target cannot be assigned and gives its SyntaxError's message.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SOURCES = {"call": "f() = 1", "genexp": "(x for x in y) = 1", "grouped genexp": "((x for x in y)) = 1", "tuple": "(a, f()) = 1",
           "chained": "a = (x for x in y), c = 1"}


def outcome(target):
    try:
        compile(SOURCES[target] + "\n", "<assign>", "exec")
    except SyntaxError as e:
        return e.msg
    return "ok"


check_programs(outcome)
