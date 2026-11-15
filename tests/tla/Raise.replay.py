# Replays Raise.tla: each case runs the spec's raise statement, alone or in
# a handler, and compares the exception and its chaining with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


class NotAnException:
    pass


log = []


class PyError(ValueError):
    def __init__(self):
        log.append("e")


class PyCause(TypeError):
    def __init__(self):
        log.append("c")


class Returns(ValueError):
    def __init__(self):
        return 1


class PyNew(ValueError):
    def __new__(cls):
        log.append("n")
        return super().__new__(cls)

    def __init__(self):
        log.append("i")


class NewInt(ValueError):
    def __new__(cls):
        log.append("n")
        return 5


class Renew(ValueError):
    def __new__(cls, *args):
        log.append("r")
        return super().__new__(cls, *args) if args else KeyError()


class NewOther(TypeError):
    def __new__(cls):
        log.append("m")
        return KeyError()

    def __init__(self):
        log.append("never")


WHATS = {"class": "ValueError", "instance": "ValueError()", "int": "5", "other": "NotAnException", "python": "PyError",
         "returns": "Returns", "new": "PyNew", "new_int": "NewInt",
         "renew": "Renew"}
CAUSES = {"class": "TypeError", "instance": "TypeError()", "None": "None", "int": "5", "python": "PyCause",
          "new_other": "NewOther"}


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
    # The statement runs in a function, as compiled code, and at module level.
    results = []
    for code in ("def f():\n" + "".join("    " + line + "\n" for line in body.split("\n")) + "f()", body):
        del log[:]
        try:
            exec(code, {"NotAnException": NotAnException, "PyError": PyError, "PyCause": PyCause, "Returns": Returns,
                         "PyNew": PyNew, "NewInt": NewInt, "NewOther": NewOther,
                         "Renew": Renew})
        except BaseException as error:
            results.append("%s cause=%s context=%s suppress=%s log=%s" % (
                type(error).__name__, name(error.__cause__), name(error.__context__), error.__suppress_context__, "".join(log)))
        else:
            results.append("no exception")
    return results[0] if results[0] == results[1] else " / ".join(results)
    return "no exception"


check_programs(outcome)
