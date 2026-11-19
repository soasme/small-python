# Replays Sets.tla: each case builds the spec's sets, applies the
# operation, and compares the type and elements (numbers as spelled), the
# bool, or the exception, with the model's. With eq, the elements are
# objects whose Python __eq__, which loops, compares their values. A hashed
# build logs its objects' Python __hash__ calls, which loop, and its
# generator's items, as does an iterable method of one.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SOURCES = {"|": "r = a | b", "&": "r = a & b", "-": "r = a - b", "^": "r = a ^ b", "<=": "r = a <= b", "<": "r = a < b",
           ">=": "r = a >= b", ">": "r = a > b", "==": "r = a == b", "isdisjoint": "r = a.isdisjoint(b)", "<= <=": "r = a <= b <= a",
           "|=": "a |= b\nr = a", "&=": "a &= b\nr = a", "-=": "a -= b\nr = a", "^=": "a ^= b\nr = a",
           "add": "a.add(2)\nr = a", "discard": "a.discard(2)\nr = a", "remove": "a.remove(2)\nr = a",
           "hash": "hash(a)\nr = 'hashable'", "add list": "a.add([])\nr = a",
           "issubset": "r = a.issubset(b)", "issuperset": "r = a.issuperset(b)"}
for name in ("union", "intersection", "difference", "symmetric_difference"):
    SOURCES[name] = "r = a.%s(b)" % name
    SOURCES[name + "_update" if name != "union" else "update"] = "assert a.%s(b) is None\nr = a" % (name + "_update" if name != "union" else "update")
MERGES = {"set": "r = set(src)", "frozenset": "r = frozenset(src)", "star": "r = {*src}", "union": "r = set().union(src)",
          "update": "r = set()\nr.update(src)", "|=": "r = set()\nr |= src", "S": "r = S(src)", "F": "r = F(src)"}


class S(set): pass
class F(frozenset): pass
class SI(set):
    def __init__(self, source): super().__init__(source)
class SN(set):
    def __new__(cls, source): return super().__new__(cls)


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
    def __eq__(self, other):
        for _ in range(2): pass
        self.log.append("e%d" % self.v)
        return self.v == other.v


def hashed(p):
    log, values = [], (1, 1) if p["fails"] == "equal" else (1, 2)
    def item(v):
        return (K(v, log, p["fails"]), 0) if p["tuple"] else K(v, log, p["fails"])
    def generator():
        for v in values:
            log.append("y%d" % v)
            yield item(v)
    source = generator() if p["source"] == "generator" else [item(v) for v in values]
    try:
        if p["form"] == "update":
            r = {0}
            r.update(source)
        elif p["form"] == "init":
            r = {0}
            set.__init__(r, source)
        elif p["form"] == "SI":
            r = SI(source)
        elif p["form"] == "SN":
            r = SN(source)
        else:
            build = {"set": set, "frozenset": frozenset, "S": S, "F": F}.get(p["form"], lambda source: {*source})
            r = build(source)
    except TypeError as error:
        return ("TypeError: " + str(error), " ".join(log), frozenset())
    except ValueError:
        return ("ValueError", " ".join(log), frozenset())
    return (type(r).__name__, " ".join(log), frozenset(getattr(v[0] if type(v) is tuple else v, "v", v) for v in r))


class C:
    def __init__(self, v, log): self.v, self.log = v, log
    def __hash__(self): return 0
    def __eq__(self, other):
        self.log.append("e")
        return self is other


def merged(p):
    log = []
    namespace = {"src": {C(v, log) for v in (0, 1, 2)}, "S": S, "F": F}
    del log[:]
    exec(MERGES[p["form"]], namespace)
    r = namespace["r"]
    return (type(r).__name__, " ".join(log), frozenset(v.v for v in r))


def iterable(p):
    log = []
    a = {"set": set, "S": S}[p["kind"]]([K(1, log, "no")])
    def generator():
        for v in (1, 2):
            log.append("y%d" % v)
            yield K(v, log, "no")
    items = [K(1, log, "no"), K(2, log, "no")]
    source = generator() if p["source"] == "generator" else iter(items) if p["source"] == "iterator" else items
    del log[:]
    if p["form"] == "argument":
        # The operands of a call as another's argument, names, need no steps.
        space = {"a": a, "source": source, "keep": lambda v: v}
        exec("r = keep(a.%s(source))" % p["method"], space)
        r = space["r"]
    else:
        r = getattr(a, p["method"])(source)
    if r is None:
        r = a
    if type(r) is bool:
        return ("bool", " ".join(log), frozenset())
    return (type(r).__name__, " ".join(log), frozenset(v.v for v in r))


def sources(p):
    log = []
    a = {K(1, log, "no")}
    def source(v):
        if p["source"] == "list":
            return [K(v, log, "no")]
        def generator():
            log.append("y%d" % v)
            yield K(v, log, "no")
        return generator()
    given = [source(v) for v in range(1, p["count"] + 1)]
    del log[:]
    r = getattr(a, p["method"])(*given) if p["count"] > 2 else getattr(a, p["method"])(given[0], given[1])
    if r is None:
        r = a
    return (type(r).__name__, " ".join(log), frozenset(v.v for v in r))


class SH(set):
    def __init__(self, items, log):
        super().__init__(items)
        self.log = log
    def __hash__(self):
        self.log.append("h")
        raise TypeError("SH")
SETKEY = {"in": "r = key in a", "not in": "r = key not in a", "discard": "a.discard(key)\n    r = a",
          "remove": "a.remove(key)\n    r = a", "add": "a.add(key)\n    r = a"}


def setkey(p):
    log = []
    key = {"set": lambda: {1}, "S": lambda: S({1}), "SH": lambda: SH({1}, log)}[p["key"]]()
    space = {"a": {frozenset({1}), 0} if p["present"] else {0}, "key": key}
    try:
        exec("def run(a, key):\n    %s\n    return r\nr = run(a, key)" % SETKEY[p["use"]], space)
    except KeyError as error:
        return ("KeyError" if error.args == (key,) else repr(error.args), " ".join(log), frozenset())
    except TypeError:
        return ("TypeError", " ".join(log), frozenset())
    r = space["r"]
    if type(r) is bool:
        return (repr(r), " ".join(log), frozenset())
    return (type(r).__name__, " ".join(log), frozenset(1 if v == frozenset({1}) else v for v in r))


def outcome(p):
    if p["op"] == "setkey":
        return setkey(p)
    if p["op"] == "iterable":
        return iterable(p)
    if p["op"] == "sources":
        return sources(p)
    if p["op"] == "hashed":
        return hashed(p)
    if p["op"] == "merge":
        return merged(p)
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
    if (p["op"] in ("|=", "&=", "-=", "^=") or p["op"].endswith("update")) and p["ka"] == "set" and r is not a:
        return ("not in place", "", frozenset())
    return (type(r).__name__, "", frozenset(getattr(v, "v", v) for v in r))


check_programs(outcome)
