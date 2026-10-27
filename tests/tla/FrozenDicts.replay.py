# Replays FrozenDicts.tla: each case builds the spec's mappings, applies
# the operation, and compares the result's type and items in order, the
# bool, or the exception, with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SOURCES = {"hash": "hash(x)", "hash list": "hash(kind_x(a=[]))", "setitem": "x['a'] = 1", "delitem": "del x['a']",
           "pop": "x.pop('a', None)", "update": "x.update()", "setdefault": "x.setdefault('a')", "clear": "x.clear()",
           "popitem": "x.popitem"}


def outcome(p):
    if p["op"] == "build":
        kind, positional = p["positional"]
        f = frozendict(**dict(p["keywords"])) if kind == "none" else frozendict(list(positional), **dict(p["keywords"]))
        return (type(f).__name__, "", tuple(f.items()))
    kinds = {"dict": dict, "frozendict": frozendict}
    x, y = kinds[p["kx"]](p["x"]), kinds[p["ky"]](p["y"])
    op = p["op"]
    if op == "|":
        r = x | y
        return (type(r).__name__, "", tuple(r.items()))
    if op == "==":
        return ("bool", repr(x == y), ())
    if op == "|=":
        z = x
        before = tuple(z.items())
        x |= y
        if type(z) is dict:
            alias = "same" if z is x else "rebound"
        else:
            alias = "kept" if tuple(z.items()) == before else "changed"
        return (type(x).__name__, alias, tuple(x.items()))
    if op == "copy":
        return ("bool", repr(x.copy() is x), ())
    if op == "isdict":
        return ("bool", repr(isinstance(x, dict)), ())
    try:
        exec(SOURCES[op], {"x": x, "kind_x": kinds[p["kx"]]})
    except (TypeError, AttributeError) as error:
        return (type(error).__name__, "", ())
    except KeyError:
        pass  # a dict without the key: the operation exists
    return ("hashable" if op == "hash" else "mutable", "", ())


check_programs(outcome)
