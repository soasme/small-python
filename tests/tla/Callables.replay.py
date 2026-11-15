# Replays Callables.tla: each case defines the spec's class, calls it (and
# the instance), and compares the result, or the exception, with the
# model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

# Each method loops, so that it runs on the machine.
LOOP = "        for _ in (): pass\n"
NEW = {"none": "", "self": "    def __new__(cls, *args, **kw):\n" + LOOP + "        return super().__new__(cls)\n",
       "other": "    def __new__(cls, *args, **kw):\n" + LOOP + "        return 5\n"}
INIT = {"none": "", "records": "    def __init__(self, *args, **kw):\n" + LOOP + "        self.args = args + tuple(kw.items())\n",
        "returns": "    def __init__(self, *args, **kw):\n" + LOOP + "        return 1\n"}
CALL = {"none": "", "class": "    def __call__(self, *a):\n        return a\n", "instance": "", "meta": "", "super": ""}
META = {"meta": "class M(type):\n    def __call__(cls, *a):\n        return a\n",
        "super": "class M(type):\n    def __call__(cls, *a, **k):\n" + LOOP + "        return super().__call__(*a, **k)\n"}


def describe(r):
    if type(r).__name__ == "C":
        return "C" + (" args=" + repr(r.args) if hasattr(r, "args") else "")
    return type(r).__name__ + " " + repr(r)


def outcome(p):
    namespace = {}
    meta = p["call"] in META
    header = META.get(p["call"], "") + "class C(%s%s):\n    pass\n" % (p["base"], ", metaclass=M" if meta else "")
    exec(header + NEW[p["new"]] + INIT[p["init"]] + CALL[p["call"]], namespace)
    C = namespace["C"]
    try:
        if p["op"] == "C()":
            return describe(C())
        if p["op"] == "C(1)":
            return describe(C(1))
        if p["op"] == "C(k=1)":
            return describe(C(k=1))
        c = C()
        if p["call"] == "instance" and type(c) is C:
            c.__call__ = lambda *a: a
        return repr(c(2))
    except TypeError:
        return "TypeError"


check_programs(outcome)
