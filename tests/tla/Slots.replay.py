# Replays Slots.tla: each case defines the spec's class S and compares the
# test, assignment, or definition's result with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SLOTS = {"a": ("a",), "a dict": ("a", "__dict__"), "empty": ()}


class Plain:
    pass


class P:
    __slots__ = ("p",)


def define(p, extra=None):
    body = dict(extra or {})
    if p["slots"] != "none":
        body["__slots__"] = SLOTS[p["slots"]]
    base = {"object": object, "Plain": Plain, "P": P}[p["base"]]
    return type("S", (base,), body)


def outcome(p):
    op = p["op"]
    try:
        if op == "conflict":
            define(p, {"a": 0})
            return "ok"
        S = define(p)
        s = S()
        if op == "hasdict":
            return repr(hasattr(s, "__dict__"))
        if op == "hasweakref":
            return repr(hasattr(s, "__weakref__"))
        if op in ("newattr", "seta", "setp"):
            name = {"newattr": "c", "seta": "a", "setp": "p"}[op]
            setattr(s, name, 1)
            return repr(getattr(s, name))
        if op == "unseta":
            return repr(s.a)
        T = define(p)
        T.__name__ = "T"
        s.__class__ = T
        return type(s).__name__
    except (AttributeError, ValueError, TypeError) as error:
        return type(error).__name__


check_programs(outcome)
