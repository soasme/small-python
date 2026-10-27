# Replays Mangling.tla: each case defines the spec's class, binds the name
# in the spec's way, and compares the name that is bound with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

BODIES = {
    "attr": "    {n} = 1\n",
    "self": "    def m(self):\n        self.{n} = 1\n",
    "param": "    def m(self, {n}=1):\n        return list(locals())\n",
    "kwarg": "    r = dict({n}=1)\n",
    "global": "    def m(self):\n        global {n}\n        {n} = 1\n",
}


def outcome(p):
    cls, name = "".join(p["cls"]), "".join(p["name"])
    namespace = {}
    exec("class " + cls + ":\n" + BODIES[p["how"]].format(n=name), namespace)
    c = namespace[cls]
    how = p["how"]
    if how == "attr":
        (key,) = [k for k in vars(c) if k not in ("__module__", "__dict__", "__weakref__", "__doc__", "__qualname__",
                                                  "__firstlineno__", "__static_attributes__")]
    elif how == "self":
        instance = c()
        instance.m()
        (key,) = vars(instance)
    elif how == "param":
        key = c().m()[1]
    elif how == "kwarg":
        (key,) = c.r
    else:
        c().m()
        (key,) = [k for k, v in namespace.items() if type(v) is int and v == 1]
    return key


check_programs(outcome)
