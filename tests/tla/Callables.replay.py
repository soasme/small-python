# Replays Callables.tla: each case defines the spec's class, calls it (and
# the instance), and compares the result, or the exception, with the
# model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

NEW = {"none": "", "self": "    def __new__(cls, *args):\n        return super().__new__(cls)\n",
       "other": "    def __new__(cls, *args):\n        return 5\n"}
INIT = {"none": "", "records": "    def __init__(self, *args):\n        self.args = args\n",
        "returns": "    def __init__(self, *args):\n        return 1\n"}
CALL = {"none": "", "class": "    def __call__(self, *a):\n        return a\n", "instance": ""}


def describe(r):
    if type(r).__name__ == "C":
        return "C" + (" args=" + repr(r.args) if hasattr(r, "args") else "")
    return type(r).__name__ + " " + repr(r)


def outcome(p):
    namespace = {}
    exec("class C:\n    pass\n" + NEW[p["new"]] + INIT[p["init"]] + CALL[p["call"]], namespace)
    C = namespace["C"]
    try:
        if p["op"] == "C()":
            return describe(C())
        if p["op"] == "C(1)":
            return describe(C(1))
        c = C()
        if p["call"] == "instance" and type(c) is C:
            c.__call__ = lambda *a: a
        return repr(c(2))
    except TypeError:
        return "TypeError"


check_programs(outcome)
