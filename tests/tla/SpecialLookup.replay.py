# Replays SpecialLookup.tla: each case defines the spec's special method
# somewhere, invokes it, and compares the result and whether
# __getattribute__ saw the name with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

IMPLEMENTATIONS = {"__len__": lambda self: 5, "__iter__": lambda self: iter([5]), "__bool__": lambda self: False,
                   "__call__": lambda self: 5, "__neg__": lambda self: 5}
SIXES = {"__len__": lambda self: 6, "__iter__": lambda self: iter([6]), "__bool__": lambda self: True,
         "__call__": lambda self: 6, "__neg__": lambda self: 6}
IMPLICIT = {"__len__": len, "__iter__": lambda x: list(iter(x)), "__bool__": bool, "__call__": lambda x: x(),
            "__neg__": lambda x: -x}


def result(m, v):
    if m == "__iter__" and not isinstance(v, (int, str)) and type(v).__name__.endswith("iterator"):
        v = list(v)
    if m == "__call__" and type(v).__name__ == "C":
        return "a C"
    return repr(v)


def outcome(p):
    m, where = p["method"], p["where"]
    seen = []
    meta_body = {m: IMPLEMENTATIONS[m]} if where == "metaclass" else {}
    Meta = type("Meta", (type,), meta_body)
    base_body = {m: IMPLEMENTATIONS[m]} if where == "base" else {}
    B = type("B", (), base_body)
    body = {m: IMPLEMENTATIONS[m]} if where in ("class", "replaced", "deleted") else {}
    if p["getattribute"]:
        def __getattribute__(self, name):
            seen.append(name)
            return object.__getattribute__(self, name)
        body["__getattribute__"] = __getattribute__
    C = Meta("C", (B,), body)
    c = C()
    if where == "instance":
        object.__setattr__(c, m, lambda: IMPLEMENTATIONS[m](None))
    if where == "replaced":
        setattr(C, m, SIXES[m])
    if where == "deleted":
        delattr(C, m)
    del seen[:]
    op = p["op"]
    try:
        if op == "explicit":
            value = result(m, getattr(c, m)())
        else:
            value = result(m, IMPLICIT[m](C if op == "onclass" else c))
    except (TypeError, AttributeError) as error:
        value = type(error).__name__
    return value + " seen=" + repr(m in seen)


check_programs(outcome)
