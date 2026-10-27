# Replays Sets.tla: each case builds the spec's sets, applies the
# operation, and compares the type and elements (numbers as spelled), the
# bool, or the exception, with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SOURCES = {"|": "r = a | b", "&": "r = a & b", "-": "r = a - b", "^": "r = a ^ b", "<=": "r = a <= b", "<": "r = a < b",
           ">=": "r = a >= b", ">": "r = a > b", "==": "r = a == b", "isdisjoint": "r = a.isdisjoint(b)",
           "|=": "a |= b\nr = a", "&=": "a &= b\nr = a", "-=": "a -= b\nr = a", "^=": "a ^= b\nr = a",
           "add": "a.add(2)\nr = a", "discard": "a.discard(2)\nr = a", "remove": "a.remove(2)\nr = a",
           "hash": "hash(a)\nr = 'hashable'", "add list": "a.add([])\nr = a"}


def outcome(p):
    if p["op"] == "build":
        r = set(eval(s) for s in p["items"])
        return ("set", "", frozenset(repr(v) for v in r))
    kinds = {"set": set, "frozenset": frozenset}
    a, b = kinds[p["ka"]](p["a"]), kinds[p["kb"]](p["b"])
    namespace = {"a": a, "b": b}
    try:
        exec(SOURCES[p["op"]], namespace)
    except (AttributeError, KeyError, TypeError) as error:
        return (type(error).__name__, "", frozenset())
    r = namespace["r"]
    if r == "hashable":
        return ("hashable", "", frozenset())
    if type(r) is bool:
        return ("bool", repr(r), frozenset())
    if p["op"] in ("|=", "&=", "-=", "^=") and p["ka"] == "set" and r is not a:
        return ("not in place", "", frozenset())
    return (type(r).__name__, "", frozenset(r))


check_programs(outcome)
