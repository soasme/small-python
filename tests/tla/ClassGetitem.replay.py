# Replays ClassGetitem.tla: each case defines the spec's class C and
# compares the subscription's result with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def user(p):
    body = {}
    if p["cg"] == "plain":
        body["__class_getitem__"] = lambda cls, key: "cg %s %s" % (cls.__name__, key.__name__)
    elif p["cg"] == "classmethod":
        body["__class_getitem__"] = classmethod(lambda cls, key: "cg %s %s" % (cls.__name__, key.__name__))
    if p["item"]:
        body["__getitem__"] = lambda self, key: "item"
    meta = type("Meta", (type,), {"__getitem__": lambda cls, key: "meta"}) if p["meta"] else type
    C = meta("C", (), body)
    return C[int] if p["subject"] == "class" else C()[int]


def outcome(p):
    try:
        if p["part"] == "user":
            return user(p)
        return repr({"list": lambda: list[int], "dict": lambda: dict[str, int], "tuple": lambda: tuple[int, ...],
                     "type": lambda: type[int]}[p["name"]]())
    except TypeError as error:
        return type(error).__name__


check_programs(outcome)
