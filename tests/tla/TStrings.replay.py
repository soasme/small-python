# Replays TStrings.tla: each case evaluates t'<body>' with x bound to an
# object that shows its format spec, and compares the Template, spelled as
# its text with [expression|conversion|spec|type] for each interpolation,
# or the exception, with the model's.
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
        template = eval(compile("t'" + "".join(p) + "'", "<program>", "eval"), {"x": F()})
    except (SyntaxError, NameError, ValueError, TypeError) as error:
        return (type(error).__name__, "")
    text = template.strings[0]
    for i, s in zip(template.interpolations, template.strings[1:]):
        text += "[%s|%s|%s|%s]" % (i.expression, i.conversion, i.format_spec, type(i.value).__name__) + s
    return ("str", text)


check_programs(outcome)
