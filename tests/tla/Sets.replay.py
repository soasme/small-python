# Replays Sets.tla: each case builds the spec's sets, applies the
# operation, and compares the type and elements (numbers as spelled), the
# bool, or the exception, with the model's. With eq, the elements are
# objects whose Python __eq__, which loops, compares their values. A hashed
# build logs its objects' Python __hash__ calls, which loop, and its
# generator's items.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SOURCES = {"|": "r = a | b", "&": "r = a & b", "-": "r = a - b", "^": "r = a ^ b", "<=": "r = a <= b", "<": "r = a < b",
           ">=": "r = a >= b", ">": "r = a > b", "==": "r = a == b", "isdisjoint": "r = a.isdisjoint(b)", "<= <=": "r = a <= b <= a",
           "|=": "a |= b\nr = a", "&=": "a &= b\nr = a", "-=": "a -= b\nr = a", "^=": "a ^= b\nr = a",
           "add": "a.add(2)\nr = a", "discard": "a.discard(2)\nr = a", "remove": "a.remove(2)\nr = a",
           "hash": "hash(a)\nr = 'hashable'", "add list": "a.add([])\nr = a"}


class E:
    def __init__(self, v): self.v = v
    def __hash__(self): return hash(self.v)
    def __eq__(self, other):
        for _ in range(2): pass
        return getattr(other, "v", other) == self.v


class K:
    def __init__(self, v, log, fails): self.v, self.log, self.fails = v, log, fails
    def __hash__(self):
        for _ in range(2): pass
        self.log.append("h%d" % self.v)
        if self.v == 2 and self.fails == "TypeError": raise TypeError("t")
        if self.v == 2 and self.fails == "ValueError": raise ValueError("v")
        return self.v


def hashed(p):
    log = []
    def generator():
        for v in (1, 2):
            log.append("y%d" % v)
            yield K(v, log, p["fails"])
    source = generator() if p["source"] == "generator" else [K(v, log, p["fails"]) for v in (1, 2)]
    try:
        if p["form"] == "update":
            r = {0}
            r.update(source)
        else:
            r = set(source) if p["form"] == "set" else frozenset(source) if p["form"] == "frozenset" else {*source}
    except TypeError as error:
        return ("TypeError: " + str(error), " ".join(log), frozenset())
    except ValueError:
        return ("ValueError", " ".join(log), frozenset())
    return (type(r).__name__, " ".join(log), frozenset(getattr(v, "v", v) for v in r))


def outcome(p):
    if p["op"] == "hashed":
        return hashed(p)
    if p["op"] == "build":
        r = set(eval(s) for s in p["items"])
        return ("set", "", frozenset(repr(v) for v in r))
    kinds = {"set": set, "frozenset": frozenset}
    wrap = E if p["eq"] else int
    a, b = kinds[p["ka"]](map(wrap, p["a"])), kinds[p["kb"]](map(wrap, p["b"]))
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
    return (type(r).__name__, "", frozenset(getattr(v, "v", v) for v in r))


check_programs(outcome)
