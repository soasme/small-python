# Replays Descriptors.tla: each case builds a descriptor class with the
# spec's methods, binds it, and compares the result and dictionary with
# the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def read(op, a, A, B, label):
    if op == "get":
        return label(a.x)
    if op == "classget":
        return label(A.x)
    if op == "superget":
        return label(super(A, a).x)
    return label(B.__dict__["x"].__get__(a))


def outcome(p):
    names = {}

    def label(v):
        if type(v) is str and v.startswith("get("):
            return v
        return names.get(id(v), repr(v))

    def __get__(self, instance, owner=None):
        return "get(%s, %s)" % (label(instance), label(owner))

    def __set__(self, instance, value):
        return names.setdefault("calls", []).append("set(%s, %r)" % (label(instance), value))

    def __delete__(self, instance):
        return names.setdefault("calls", []).append("delete(%s)" % label(instance))

    body = {}
    methods = p["methods"]
    if "get" in methods:
        body["__get__"] = __get__
    if "set" in methods:
        body["__set__"] = __set__
    if "delete" in methods:
        body["__delete__"] = __delete__
    D = type("D", (), body)
    d = D()
    B = type("B", (), {"x": d})
    A = type("A", (B,), {"x": 999} if p["op"] == "superget" else {})
    a = A()
    names.update({id(a): "a", id(A): "A", id(None): "None", id(d): "D"})
    if p["dict"]:
        a.__dict__["x"] = "inst"
    op = p["op"]
    try:
        if op in ("get", "classget", "superget", "direct"):
            return read(op, a, A, B, label)
    except AttributeError:
        return "AttributeError"
    try:
        if op == "classset":
            A.x = 1
            return "None " + repr(A.__dict__["x"])
        if op == "set":
            a.x = 1
        else:
            del a.x
        result = " ".join(names.get("calls", [])) or "None"
    except AttributeError:
        result = "AttributeError"
    return result + " " + repr(a.__dict__)


check_programs(outcome)
