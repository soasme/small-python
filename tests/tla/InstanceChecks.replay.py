# Replays InstanceChecks.tla: each case defines the spec's classes and
# compares isinstance() or issubclass() with the model's result.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def hooks(kind):
    def check(cls, other):
        if kind == "raise":
            raise ValueError
        return 1 if kind == "true" else 0
    return {"__instancecheck__": check, "__subclasscheck__": check}


def outcome(p):
    hook = p["hook"]
    if hook in ("true", "false", "raise"):
        C = type("Meta", (type,), hooks(hook))("C", (), {})
    else:
        C = type("C", (), hooks("true") if hook == "onclass" else {})
    D = type("D", (C,), {})
    cls = {"C": C, "tuple": (str, C), "five": 5}[p["cls"]]
    try:
        if p["check"] == "isinstance":
            result = isinstance({"C": C, "D": D, "int": int}[p["subject"]]() if p["subject"] != "int" else 1, cls)
        else:
            result = issubclass({"C": C, "D": D, "int": int}[p["subject"]], cls)
        return repr(result)
    except (ValueError, TypeError) as error:
        return type(error).__name__


check_programs(outcome)
