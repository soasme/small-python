# Replays ClassObjects.tla: each case defines the spec's class C and
# compares the attribute or operation's result (classes by name), or the
# exception, with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def source(p):
    params = "[T]" if p["generic"] else ""
    bases = "(" + ", ".join(p["bases"]) + ")" if p["bases"] else ""
    body = ("'doc'\n" if p["doc"] else "") + ("x: int\n" if p["ann"] else "") + \
        "def m(self):\n    self.b = 1\n    self.a = 2\n"
    cls = "class C" + params + bases + ":\n" + "".join("    " + line + "\n" for line in body.splitlines())
    head = "class A:\n    w = 0\nclass B: pass\n".replace("class A:\n    w = 0\n", "class A: w = 0\n")
    if p["nested"]:
        return head + "def f():\n" + "".join("    " + line + "\n" for line in cls.splitlines()) + "    return C\nC = f()\n"
    return head + cls


def name(v):
    if type(v) is type:
        return v.__name__
    if type(v) is tuple:
        return "(" + ", ".join(name(x) for x in v) + ("," if len(v) == 1 else "") + ")"
    if type(v) is list:
        return "[" + ", ".join(name(x) for x in v) + "]"
    if type(v) is dict and all(type(x) is type for x in v.values()):
        return "{" + ", ".join(repr(k) + ": " + x.__name__ for k, x in v.items()) + "}"
    return repr(v)


def outcome(p):
    namespace = {"__name__": "m"}
    exec(source(p), namespace)
    C, A = namespace["C"], namespace["A"]
    op = p["op"]
    try:
        if op == "read":
            v = getattr(C, p["attr"])
            if p["attr"] == "__dict__":
                return type(v).__name__
            if p["attr"] == "__annotate__":
                return "None" if v is None else "function"
            return name(v)
        if op == "dictwrite":
            C.__dict__["x"] = 1
            return "written"
        if op == "subdoc":
            return repr(type("D", (C,), {}).__doc__)
        if op == "subclasses":
            return name(A.__subclasses__())
        if op == "classset":
            C.w = 1
            return repr(A.w)
        c = C() if int not in C.__mro__ else C(0)
        if op == "instanceset":
            c.w = 5
            return repr(C.w)
        if op == "instancedict":
            c.z = 1
            return repr(c.__dict__)
        return name(c.__class__)
    except (TypeError, AttributeError) as error:
        return type(error).__name__


check_programs(outcome)
