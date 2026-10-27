# Replays FStrings.tla: each case evaluates f'<body>' with x bound to an
# object that shows its format spec, and compares the string, or the
# exception, with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


class F:
    def __format__(self, spec):
        return "<" + spec + ">"

    def __repr__(self):
        return "R"

    def __eq__(self, other):
        return self

    def __ne__(self, other):
        return self


def outcome(p):
    try:
        value = eval(compile("f'" + "".join(p) + "'", "<program>", "eval"), {"x": F()})
    except (SyntaxError, NameError, ValueError, TypeError) as error:
        return (type(error).__name__, "")
    return ("str", value)


check_programs(outcome)
