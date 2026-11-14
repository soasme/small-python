# Replays SetWalks.tla: each case builds a and b of objects of one hash
# whose Python __eq__ (which loops) logs its side and value, applies the
# operation in a function that runs on the machine and in one that runs
# in C, and compares the result's values, or the bool, and the log with
# the model's outcome.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

log = []


class E:
    def __init__(self, side, v): self.side, self.v = side, v
    def __hash__(self): return 1
    def __eq__(self, other):
        for _ in (): pass  # a loop: __eq__ runs on the machine
        log.append(self.side + str(self.v))
        return self.v == other.v


SOURCES = {"|=": "a |= b\nr = a", "&=": "a &= b\nr = a", "-=": "a -= b\nr = a", "^=": "a ^= b\nr = a"}


def source(op):
    if op in SOURCES: return SOURCES[op]
    if op.endswith("update"): return "a.%s(b)\nr = a" % op
    if op in ("union", "intersection", "difference", "symmetric_difference", "issubset", "issuperset", "isdisjoint"):
        return "r = a.%s(b)" % op
    return "r = a %s b" % op


def run(p, machine):
    for _ in (): pass
    kind = set if p["ka"] == "set" else frozenset
    a = kind(E("a", v) for v in sorted(p["a"]))
    b = {E("b", v) for v in sorted(p["b"])}
    body = source(p["op"]).replace("\n", "\n    ")
    loop = "    for _ in (): pass\n" if machine else ""
    scope = {}
    exec("def f(a, b):\n" + loop + "    " + body + "\n    return r\n", scope)
    log.clear()
    r = scope["f"](a, b)
    shown = repr(r) if isinstance(r, bool) else "{" + "".join(str(v) for v in sorted(e.v for e in r)) + "}"
    return " ".join([shown] + log)


def outcome(p):
    machine = run(p, True)
    walker = run(p, False)
    return machine if machine == walker else "machine " + machine + " | C " + walker


check_programs(outcome)
