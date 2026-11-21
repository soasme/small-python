# Replays PropertyMethods.tla: each case makes the property and calls its
# __set__, __delete__ or __get__ as the program says, then writes the result and the
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


def got(p):
    calls = []

    class Getter:
        def __call__(self, obj):
            for _ in (): pass
            calls.append("get(c)")
            if p["function"] == "raises": raise LookupError
            return "got"

    maker = property if p["maker"] == "property" else Sub
    C = type("C", (), {"x": maker(None if p["function"] == "absent" else Getter())})
    c = C()
    x = C.__dict__["x"]
    read = {"method": lambda: x.__get__(c), "class": lambda: maker.__get__(x, c, C),
            "bound": x.__get__, "statement": lambda: c.x}[p["how"]]
    try:
        result = repr(read(c) if p["how"] == "bound" else read())
    except LookupError:
        result = "LookupError"
    except AttributeError as e:
        return "AttributeError " + ("getter" if "getter" in str(e) else str(e))
    return " ".join([result] + calls)


def named(p):
    calls = []

    class Getter:
        def __call__(self, obj): return 0

        @property
        def __name__(self):
            for _ in (): pass
            calls.append("name")
            if p["function"] == "raises": raise LookupError
            if p["function"] == "absent": raise AttributeError
            return "nm"

    class C:
        pass
    C.x = (property if p["maker"] == "property" else Sub)(Getter())
    c = C()

    x = C.__dict__["x"]
    later = x.__delete__

    def run():
        if p["op"] == "callnamed":
            if p["how"] == "statement": x.__set__(c, 1)
            elif p["how"] == "method": type(x).__set__(x, c, 1)
            elif p["how"] == "class": type(x).__delete__(x, c)
            else: later(c)
        elif p["how"] == "statement": c.x = 1
        elif p["how"] == "method": setattr(c, "x", 1)
        elif p["how"] == "class": del c.x
        else: delattr(c, "x")
    try:
        run()
        result = "None"
    except LookupError:
        result = "LookupError"
    except AttributeError as e:
        text = str(e)
        quoted = text.split()[1] if text.startswith("property '") else "-"
        result = "AttributeError " + quoted + " " + text.split()[-1]
    return " ".join([result] + calls)


def outcome(p):
    if p["op"] in ("named", "callnamed"):
        return named(p)
    if p["op"] == "doc":
        return documented(p)
    if p["op"] == "get":
        return got(p)
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
    elif p["how"] == "statement":
        def call():
            if p["op"] == "set":
                c.x = 1
            else:
                del c.x
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
