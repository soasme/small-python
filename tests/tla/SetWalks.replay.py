# Replays SetWalks.tla: each case builds a and b of objects of one hash
# whose Python __eq__ (which loops) logs its side and value, applies the
# operation in a function that runs on the machine and in one that runs
# in C, an operator also by its method's name, and compares the result's
# values, or the bool, and the log with the model's outcome.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

log = []


class S(set):
    pass


KINDS = {"set": set, "frozenset": frozenset, "subset": S,
         "dict": lambda keys: dict.fromkeys(keys, 0), "frozendict": lambda keys: frozendict(dict.fromkeys(keys, 0))}


class E:
    def __init__(self, side, v): self.side, self.v = side, v
    def __hash__(self): return 1
    def __eq__(self, other):
        for _ in (): pass  # a loop: __eq__ runs on the machine
        log.append(self.side + str(self.v))
        return self.v == other.v


SOURCES = {"|=": "a |= b\nr = a", "&=": "a &= b\nr = a", "-=": "a -= b\nr = a", "^=": "a ^= b\nr = a"}
METHODS = {"|": "or", "&": "and", "-": "sub", "^": "xor", "|=": "ior", "&=": "iand", "-=": "isub", "^=": "ixor",
           "==": "eq", "!=": "ne", "<": "lt", "<=": "le", ">": "gt", ">=": "ge"}


def source(op, named, unbound=False):
    if named: return "r = a.__%s__(b)" % METHODS[op]
    if unbound: return ("m = type(a).%s\nm(a, b)\nr = a" if op.endswith("update") else "m = type(a).%s\nr = m(a, b)") % op
    if op in SOURCES: return SOURCES[op]
    if op.endswith("update"): return "a.%s(b)\nr = a" % op
    if op in ("union", "intersection", "difference", "symmetric_difference", "issubset", "issuperset", "isdisjoint"):
        return "r = a.%s(b)" % op
    return "r = a %s b" % op


METHODS_NAMED = ("union", "intersection", "difference", "symmetric_difference", "issubset", "issuperset", "isdisjoint",
                 "update", "intersection_update", "difference_update", "symmetric_difference_update")


def named_method(p):
    # frozenset has no in-place methods; a method called by name is not reflected
    return p["op"] in METHODS and hasattr(KINDS[p["ka"]], "__%s__" % METHODS[p["op"]]) and p["kb"] == "set"


def run(p, machine, named=False, unbound=False):
    for _ in (): pass
    a = KINDS[p["ka"]](E("a", v) for v in sorted(p["a"]))
    b = KINDS[p["kb"]](E("b", v) for v in sorted(p["b"]))
    body = source(p["op"], named, unbound).replace("\n", "\n    ")
    loop = "    for _ in (): pass\n" if machine else ""
    scope = {}
    exec("def f(a, b):\n" + loop + "    " + body + "\n    return r\n", scope)
    log.clear()
    r = scope["f"](a, b)
    shown = repr(r) if isinstance(r, bool) else "{" + "".join(str(v) for v in sorted(e.v for e in r)) + "}"
    return " ".join([shown] + log)


def chained(p, machine):
    a = set(E("a", v) for v in sorted(p["a"]))
    b, c = ({E(side, v) for v in sorted(p[side])} for side in ("b", "c"))
    loop = "    for _ in (): pass\n" if machine else ""
    scope = {}
    exec("def f(a, b, c):\n" + loop + "    r = a.%s(b, c)\n    return a if r is None else r\n" % p["chain"], scope)
    log.clear()
    r = scope["f"](a, b, c)
    return " ".join(["{" + "".join(str(v) for v in sorted(e.v for e in r)) + "}"] + log)


def built(p, machine):
    b = KINDS[p["kb"]](E("b", v) for v in sorted(p["b"]))
    loop = "    for _ in (): pass\n" if machine else ""
    scope = {}
    exec("def f(b):\n" + loop + "    return %s(b)\n" % p["built"], scope)
    log.clear()
    r = scope["f"](b)
    return " ".join(["{" + "".join(str(v) for v in sorted(e.v for e in r)) + "}"] + log)


def outcome(p):
    if "built" in p:
        machine, walker = built(p, True), built(p, False)
        return machine if machine == walker else "machine " + machine + " | C " + walker
    if "chain" in p:
        machine, walker = chained(p, True), chained(p, False)
        return machine if machine == walker else "machine " + machine + " | C " + walker
    machine = run(p, True)
    runs = [run(p, False)] + [run(p, machine, True) for machine in (True, False) if named_method(p)]
    # a method called unbound, given its set first
    runs += [run(p, machine, unbound=True) for machine in (True, False) if p["op"] in METHODS_NAMED]
    return machine if all(r == machine for r in runs) else "machine " + machine + " | " + " | ".join(runs)


check_programs(outcome)
