# Replays MethodDescriptors.tla: each case wraps the spec's target, takes
# it from C or D, and compares the type, call, or attribute with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()


def f(*a):
    return a


def name(v):
    if type(v) is type:
        return v.__name__
    if type(v) is tuple:
        return "(" + ", ".join(name(x) for x in v) + ("," if len(v) == 1 else "") + ")"
    return repr(v)


def outcome(p):
    target = {"f": f, "abs": abs, "5": 5}[p["target"]]
    wrap = staticmethod if p["wrap"] == "static" else classmethod

    class C:
        x = wrap(target)

    class D(C):
        pass

    access = p["access"]
    got = {"C": lambda: C.x, "C()": lambda: C().x, "D": lambda: D.x, "D()": lambda: D().x,
           "raw": lambda: C.__dict__["x"]}[access]()
    op = p["op"]
    try:
        if op == "type":
            return type(got).__name__
        if op == "call":
            return name(got(-1))
        if op in ("func", "wrapped"):
            return "the target" if getattr(got, "__" + op + "__") is target else "other"
        return repr(got.__name__)
    except (TypeError, AttributeError) as error:
        return type(error).__name__


check_programs(outcome)
