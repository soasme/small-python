# Replays SuperBinding.tla: each case binds an unbound super subclass
# object stored on a class, read through an instance or the class.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def outcome(p):
    armed = []

    class S(super):
        def __init__(self, *args):
            for _ in (): pass
            if armed:
                raise AttributeError("bound")
            self.seen = args
            super().__init__(*args)

    body = {}
    if p["fallback"]:
        def __getattr__(self, name):
            for _ in (): pass
            return "fallback"
        body["__getattr__"] = __getattr__
    B = type("B", (), body)
    d = S(B)
    B.x = d
    A = type("A", (B,), {})
    a = A()
    names = {id(a): "a", id(B): "B", id(d): "D"}

    def label(v):
        if isinstance(v, S) and v is not d:
            return "S(%s)" % ", ".join(names.get(id(x), repr(x)) for x in v.seen)
        return names.get(id(v), repr(v))

    if p["dict"]:
        a.__dict__["x"] = "inst"
    if p["raises"]:
        armed.append(1)
    op = p["op"]
    try:
        if op == "get":
            return label(a.x)
        if op == "getattr":
            return label(getattr(a, "x"))
        if op == "getattrd":
            return label(getattr(a, "x", "dflt"))
        if op == "hasattr":
            return repr(hasattr(a, "x"))
        if op == "objget":
            return label(object.__getattribute__(a, "x"))
        return label(A.x)
    except AttributeError as e:
        return "AttributeError x" if e.name == "x" else "AttributeError"


check_programs(outcome)
