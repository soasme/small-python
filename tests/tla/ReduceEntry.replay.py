# Replays ReduceEntry.tla: each case replaces the builtins entry by an
# equal key whose __eq__ runs the effect on the iterator first, then
# writes what __reduce__ returns as the model does.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

builtins = vars(iter.__self__)
MAKE = {"list": lambda: iter([1, 2]), "dict": lambda: iter({1: 2, 3: 4}), "range": lambda: iter(range(0, 4)),
        "reversed": lambda: reversed([1, 2])}


def outcome(p):
    it = MAKE[p["kind"]]()
    name = "reversed" if p["kind"] == "reversed" else "iter"

    class Key:
        def __hash__(self):
            return hash(name)

        def __eq__(self, other):
            if p["effect"] == "next":
                next(it)
            elif p["effect"] == "drain":
                list(it)
            if p["answer"] == "raise":
                raise LookupError
            return {"name": other == name, "one": 1, "declined": NotImplemented}[p["answer"]]

    original = builtins.pop(name)
    builtins[Key()] = original
    try:
        result = it.__reduce__()
    except (LookupError, AttributeError) as e:
        return type(e).__name__
    finally:
        for key in [key for key in builtins if type(key) is Key]:
            del builtins[key]
        builtins[name] = original
    head = result[0].__name__
    return "(%s, %s%s)" % (head, repr(result[1]), "".join(", " + repr(item) for item in result[2:]))

check_programs(outcome)
