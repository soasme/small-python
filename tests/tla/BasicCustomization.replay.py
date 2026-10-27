# Replays BasicCustomization.tla: each case defines the spec's classes and
# compares the comparison, hash, truth, or text conversion with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def methods(kind, owner, names):
    body = {}
    for name in names:
        if kind == "value":
            body["__%s__" % name] = (lambda text: lambda self, other: text)(owner + "." + name)
        elif kind == "notimpl":
            body["__%s__" % name] = lambda self, other: NotImplemented
    return body


def compare(p):
    A = type("A", (), methods(p["a"], "A", ("eq", "lt")))
    S = type("S", (A,), methods(p["s"], "S", ("eq", "gt")))
    O = type("O", (), methods(p["o"], "O", ("eq", "gt")))
    left, right = A(), {"A": A, "S": S, "O": O}[p["right"]]()
    op = p["op"]
    result = {"==": lambda: left == right, "!=": lambda: left != right, "<": lambda: left < right,
              ">": lambda: left > right}[op]()
    return result if type(result) is str else repr(result)


def outcome(p):
    part = p["part"]
    try:
        if part == "compare":
            return compare(p)
        if part == "hash":
            body = {}
            if p["eq"]:
                body["__eq__"] = lambda self, other: self is other
            if p["hash"] != "none":
                body["__hash__"] = None if p["hash"] == "None" else (lambda self: 5)
            h = hash(type("H", (), body)())
            return "5" if h == 5 else "an int"
        if part == "truth":
            body = {}
            if p["bool"] != "none":
                body["__bool__"] = {"True": lambda self: True, "False": lambda self: False, "one": lambda self: 1}[p["bool"]]
            if p["len"] != "none":
                body["__len__"] = (lambda n: lambda self: n)(int(p["len"]))
            return repr(bool(type("T", (), body)()))
        body = {}
        if p["repr"]:
            body["__repr__"] = lambda self: "r"
        if p["str"]:
            body["__str__"] = lambda self: "s"
        x = type("X", (), body)()
        text = {"str": str, "repr": repr, "format": lambda v: format(v, "")}[p["op"]](x)
        return "<default>" if text.startswith("<") else repr(text)
    except (TypeError, ValueError) as error:
        return type(error).__name__


check_programs(outcome)
