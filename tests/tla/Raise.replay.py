# Replays Raise.tla: each case runs the spec's raise statement, alone or in
# a handler, and compares the exception and its chaining with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


class NotAnException:
    pass


WHATS = {"class": "ValueError", "instance": "ValueError()", "int": "5", "other": "NotAnException"}
CAUSES = {"class": "TypeError", "instance": "TypeError()", "None": "None", "int": "5"}


def statement(p):
    if p["what"] == "bare":
        return "raise"
    if p["what"] == "divide":
        return "1 / 0"
    text = "raise " + WHATS[p["what"]]
    if p["cause"] != "absent":
        text += " from " + CAUSES[p["cause"]]
    return text


def name(value):
    return "None" if value is None else type(value).__name__


def outcome(p):
    body = statement(p)
    if p["handling"]:
        body = "try:\n    raise KeyError\nexcept KeyError:\n    " + body
    try:
        exec(body, {"NotAnException": NotAnException})
    except BaseException as error:
        return "%s cause=%s context=%s suppress=%s" % (
            type(error).__name__, name(error.__cause__), name(error.__context__), error.__suppress_context__)
    return "no exception"


check_programs(outcome)
