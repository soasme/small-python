# Replays NumericProtocol.tla: each case defines the spec's classes and
# compares the addition, in-place addition, or index conversion with the
# model's result.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def method(kind, name):
    if kind == "value":
        return lambda self, other: name
    return lambda self, other: NotImplemented


def body(**kinds):
    return {"__%s__" % key: method(kind, name) for key, (kind, name) in kinds.items() if kind != "none"}


def outcome(p):
    part = p["part"]
    try:
        if part == "binary":
            A = type("A", (), body(add=(p["add"], "A.add"), radd=(p["radd"], "A.radd")))
            S = type("S", (A,), body(radd=(p["s"], "S.radd")))
            O = type("O", (), body(radd=(p["o"], "O.radd")))
            return A() + {"A": A, "S": S, "O": O}[p["right"]]()
        if part == "inplace":
            A = type("A", (), body(iadd=(p["iadd"], "A.iadd"), add=(p["add"], "A.add")))
            x = A()
            x += A()
            return x
        attrs = {}
        if p["index"] != "none":
            attrs["__index__"] = (lambda r: lambda self: r)(3 if p["index"] == "int" else 3.0)
        if p["int"]:
            attrs["__int__"] = lambda self: 7
        x = type("X", (), attrs)()
        result = {"subscript": lambda: [10, 20, 30, 40][x], "range": lambda: len(range(x)), "int": lambda: int(x)}[p["use"]]()
        return repr(result)
    except TypeError as error:
        return type(error).__name__


check_programs(outcome)
