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


def read(p):
    def key(k):
        for _ in (): pass
        return "key %s" % k.__name__
    def getattribute(cls, name):
        if name != "__class_getitem__": return type.__getattribute__(cls, name)
        if p["read"] == "missing": raise AttributeError(name)
        if p["read"] == "raising": raise KeyError(name)
        return key
    body = {}
    if p["read"] in ("getattribute", "missing", "raising"): body["__getattribute__"] = getattribute
    if p["read"] == "getattr": body["__getattr__"] = lambda cls, name: key
    if p["read"] == "meta_attribute":
        body["__class_getitem__"] = classmethod(lambda cls, k: "cg %s %s" % (cls.__name__, k.__name__))
    C = type("Meta", (type,), body)("C", (), {})
    if p["read"] == "stored": C.__class_getitem__ = key
    if p["read"] == "static": C.__class_getitem__ = staticmethod(key)
    return C[int]


def outcome(p):
    try:
        if p["part"] == "user":
            return user(p)
        if p["part"] == "read":
            return read(p)
        return repr({"list": lambda: list[int], "dict": lambda: dict[str, int], "tuple": lambda: tuple[int, ...],
                     "type": lambda: type[int]}[p["name"]]())
    except (TypeError, KeyError) as error:
        return type(error).__name__


check_programs(outcome)
