# Replays Objects.tla: each case runs the spec's statements and compares
# identities, values, and types with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

STATEMENTS = {"new a": "a = []", "new b": "b = []", "alias": "b = a", "push a": "a.append(1)",
              "push b": "b.append(1)", "wrap": "t = (a,)"}


def outcome(p):
    a = []
    b = []
    a0 = a
    t = (a,)
    for op in p:
        if op == "retype":
            try:
                a.__class__ = tuple
            except TypeError:
                pass
            continue
        namespace = {"a": a, "b": b, "t": t}
        exec(STATEMENTS[op], namespace)
        a, b, t = namespace["a"], namespace["b"], namespace["t"]
    return (a is b, id(a) == id(b), a == b, len(a), len(b), a is a0, len(t[0]), t[0] is a, type(a) is list)


check_programs(outcome)
