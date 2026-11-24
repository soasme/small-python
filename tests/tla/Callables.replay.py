# Replays Callables.tla: each case defines the spec's class, calls it (and
# the instance), and compares the result, or the exception, with the
# model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

# Each method loops, so that it runs on the machine.
LOOP = "        for _ in (): pass\n"
NEW = {"none": "", "self": "    def __new__(cls, *args, **kw):\n" + LOOP + "        return super().__new__(cls)\n",
       "other": "    def __new__(cls, *args, **kw):\n" + LOOP + "        return 5\n",
       "classmethod": "    @classmethod\n    def __new__(owner, cls, *args, **kw):\n" + LOOP + "        return super(owner, cls).__new__(cls)\n",
       "descriptor": "    __new__ = type('Get', (), {'__get__': lambda self, inst, owner: lambda cls, *a, **k: super(owner, cls).__new__(cls)})()\n"}
INIT = {"none": "", "records": "    def __init__(self, *args, **kw):\n" + LOOP + "        self.args = args + tuple(kw.items())\n",
        "returns": "    def __init__(self, *args, **kw):\n" + LOOP + "        return 1\n",
        "descriptor": "    __init__ = type('Init', (), {'__get__': lambda self, inst, owner: lambda *args, **kw:"
                      " setattr(inst, 'args', args + tuple(kw.items()))})()\n"}
CALL = {"none": "", "class": "    def __call__(self, *a):\n        return a\n", "instance": "", "meta": "", "super": "", "unbound": ""}
META = {"meta": "class M(type):\n    def __call__(cls, *a):\n        return a\n",
        "super": "class M(type):\n    def __call__(cls, *a, **k):\n" + LOOP + "        return super().__call__(*a, **k)\n",
        "unbound": "class M(type):\n    def __call__(cls, *a, **k):\n" + LOOP + "        return type.__call__(cls, *a, **k)\n"}


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

    class Box:
        pass
    box = [Box()]
    box[0].C = C
    attribute = p["via"] == "attribute"
    try:
        if p["op"] == "C()":
            return describe(box[0].C() if attribute else C())
        if p["op"] == "C(1)":
            return describe(box[0].C(1) if attribute else C(1))
        if p["op"] == "C(k=1)":
            return describe(box[0].C(k=1) if attribute else C(k=1))
        c = box[0].C() if attribute else C()
        if p["call"] == "instance" and type(c) is C:
            c.__call__ = lambda *a: a
        box[0].c = c
        return repr(box[0].c(2) if attribute else c(2))
    except TypeError:
        return "TypeError"


check_programs(outcome)
