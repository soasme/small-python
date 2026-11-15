# Replays InstanceChecks.tla: each case defines the spec's classes and
# compares isinstance() or issubclass() with the model's result. A hook's
# result of truthy or empty is an object whose Python __bool__ or __len__
# gives its truth.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


class Truthy:
    def __bool__(self):
        for _ in ():  # a loop: the method runs on the machine
            pass
        return True


class Empty:
    def __len__(self):
        for _ in ():
            pass
        return 0


RESULTS = {"true": lambda: 1, "false": lambda: 0, "truthy": Truthy, "empty": Empty}


def hooks(kind):
    def check(cls, other):
        for _ in ():  # a loop: the hook runs on the machine
            pass
        if kind == "raise":
            raise ValueError
        return RESULTS[kind]()
    return {"__instancecheck__": check, "__subclasscheck__": check}


def outcome(p):
    hook = p["hook"]
    if hook in ("true", "false", "truthy", "empty", "raise"):
        C = type("Meta", (type,), hooks(hook))("C", (), {})
    else:
        C = type("C", (), hooks("true") if hook == "onclass" else {})
    D = type("D", (C,), {})
    cls = {"C": C, "tuple": (str, C), "pair": (C, int), "nested": ((str, (C,)),), "five": 5}[p["cls"]] if p["cls"] != "instance" else C()
    try:
        if p["check"] == "isinstance":
            result = isinstance({"C": C, "D": D, "int": int}[p["subject"]]() if p["subject"] != "int" else 1, cls)
        else:
            result = issubclass({"C": C, "D": D, "int": int}[p["subject"]], cls)
        return repr(result)
    except (ValueError, TypeError) as error:
        return type(error).__name__


check_programs(outcome)
