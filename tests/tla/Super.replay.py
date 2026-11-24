# Replays Super.tla: each case defines the spec's diamond, calls m or
# __get__ on an instance, and compares the log with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

BASES = {"A": "", "B": "(A)", "C": "(A)", "D": "(B, C)"}


FRAMES = {
    "method": "class A:\n    def m(self):\n        return super()\nA().m()\n",
    "lambda": "class A:\n    def m(self):\n        return (lambda: super())()\nA().m()\n",
    "generic": "class G[T](super()): pass\n",
}


BINDS = """log = []
class A: pass
class S(super):
    def __init__(self, *args):
        for _ in (): pass
        log.append("init"); super().__init__(*args)
"""


def bind(p):
    namespace = {}
    exec(BINDS, namespace)
    A, S, log = namespace["A"], namespace["S"], namespace["log"]
    a = A()
    cls = super if p["cls"] == "super" else S
    sup = cls(A, a) if p["bound"] else cls(A)
    log.clear()
    result = super.__get__(sup, None if p["obj"] == "None" else a, A)
    if result is sup:
        return (tuple(log), "itself")
    return (tuple(log), "%s bound" % type(result).__name__ if result.__self__ is a else "wrong")


def meta(p):
    namespace = {}
    exec("class S(super):\n" + ("    def __set__(self, o, v): pass\n" if p["set"] else "    pass\n") +
         "class MM(type):\n    __prepare__ = S(type)\nM = MM('M', (type,), {})\n", namespace)
    got = namespace["M"].__prepare__
    if isinstance(got, super):
        return ((), "S bound" if got.__self__ is namespace["M"] else "wrong")
    return ((), "type's" if got.__self__ is namespace["M"] and got.__name__ == "__prepare__" else repr(got))


def outcome(p):
    if p.get("op") == "bind":
        return bind(p)
    if p.get("op") == "meta":
        return meta(p)
    if p.get("op") == "frame":
        try:
            exec(FRAMES[p["frame"]], {})
        except RuntimeError as error:
            return ((), "RuntimeError: %s" % error)
        return ((), "ok")
    lines = []
    for c in "ABCD":
        lines.append("class %s%s:" % (c, BASES[c]))
        kind = p["kind"][c]
        if kind == "none":
            lines.append("    pass")
        elif p["name"] == "p":
            lines.append("    @property")
            lines.append("    def p(self):")
            lines.append("        for _ in (): pass")
            lines.append("        log.append(%r)" % c)
            if kind == "super":
                lines.append("        return super().p")
        else:
            lines.append("    def %s(self, *args):" % p["name"])
            lines.append("        log.append(%r)" % c)
            if kind == "super":
                lines.append("        super().%s(%s)" % (p["name"], "self" if p["name"] == "__get__" else ""))
    if p["receiver"] == "proxy":
        # Another class's object, whose __class__ answers the called class.
        lines += ["class Proxy:", "    @property", "    def __class__(self):", "        for _ in range(2): pass", "        return %s" % p["call"]]
    receiver = "%s()" % ("Proxy" if p["receiver"] == "proxy" else p["call"])
    if p["name"] == "p":
        lines.append("%s.p.fget(%s)" % (p["call"], receiver))
    else:
        lines.append("%s.%s(%s%s)" % (p["call"], p["name"], receiver, ", None" if p["name"] == "__get__" else ""))
    log = []
    try:
        exec("\n".join(lines) + "\n", {"log": log})
    except AttributeError:
        return (tuple(log), "AttributeError")
    return (tuple(log), "ok")


failures = 0
count = 0
for walk in walks():
    count += 1
    steps = states(walk)
    program = next(steps)["program"]
    for state in steps:
        actual = outcome(program)
        if actual != state["outcome"]:
            failures += 1
            if failures <= 20:
                print("MISMATCH", program, "expected", state["outcome"], "got", actual)
if failures:
    print(failures, "mismatches")
else:
    print("replayed", count, "cases")
