# Replays PropertyMethods.tla: each case makes the property and calls its
# __set__ or __delete__ as the program says, then writes the result and the
# function's calls as the model does.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


class Sub(property):
    pass


def documented(p):
    calls = []

    class Getter:
        def __call__(self, obj): return 0

        @property
        def __doc__(self):
            for _ in (): pass
            calls.append("doc")
            if p["function"] == "raises": raise LookupError
            if p["function"] == "absent": raise AttributeError
            return "documented"

    maker = property if p["maker"] == "property" else Sub
    try:
        result = repr(maker(Getter()).__doc__)
    except LookupError:
        result = "LookupError"
    return " ".join([result] + calls)


def outcome(p):
    if p["op"] == "doc":
        return documented(p)
    calls = []

    def function(self, *value):
        # A loop puts the function on the machine, as a pausing call runs it.
        for _ in (): pass
        calls.append("set(c, 1)" if value else "delete(c)")
        if p["function"] == "raises":
            raise LookupError
        return "ignored"

    given = None if p["function"] == "absent" else function
    maker = property if p["maker"] == "property" else Sub
    C = type("C", (), {"x": maker(lambda self: 0, given if p["op"] == "set" else None, given if p["op"] == "delete" else None)})
    c = C()
    name = "__set__" if p["op"] == "set" else "__delete__"
    args = (c, 1) if p["op"] == "set" else (c,)
    if p["how"] == "method":
        call = lambda: getattr(C.__dict__["x"], name)(*args)
    elif p["how"] == "class":
        call = lambda: getattr(maker, name)(C.__dict__["x"], *args)
    else:
        bound = getattr(C.__dict__["x"], name)
        call = lambda: bound(*args)
    try:
        result = repr(call())
    except LookupError:
        result = "LookupError"
    except AttributeError as e:
        return "AttributeError " + ("setter" if str(e).endswith("setter") else "deleter")
    return " ".join([result] + calls)

check_programs(outcome)
