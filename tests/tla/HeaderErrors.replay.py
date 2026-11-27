# Replays HeaderErrors.tla: each case compiles a header and gives its
# SyntaxError's message, column and end column.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SOURCES = {"def_name": "def f[T U](): pass", "def_bound": "def f[T: a b](): pass", "class_name": "class C[T U]: pass",
           "alias_equals": "type X[T] 1", "tuple_bound": "def f[*Ts: int | str](): pass",
           "spec_constraints": "def f[**P: (a, b)](): pass", "decorator": "@a b\ndef f(): pass", "import": "import\n",
           "lazy_import": "lazy import\n"}


def outcome(program):
    try:
        compile(SOURCES[program], "<header>", "exec")
    except SyntaxError as e:
        return (e.msg, e.offset, e.end_offset)
    return ("ok", 0, 0)


check_programs(outcome)
