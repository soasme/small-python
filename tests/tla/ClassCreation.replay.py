# Replays ClassCreation.tla: each case runs the spec's class statement with
# logging hooks and compares the log with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

HOOKS = '''
class D:
    def __set_name__(self, owner, name):
        log.append("set_name " + name)

class Meta(type):
    def __new__(mcls, name, bases, ns, **kw):
        log.append("new")
        return super().__new__(mcls, name, bases, ns, **kw)
    def __init__(cls, name, bases, ns, **kw):
        log.append("init")
        super().__init__(name, bases, ns)

class InitOnly(type):
    def __init__(cls, name, bases, ns, **kw):
        log.append("init")
        super().__init__(name, bases, ns)

class Logged(dict):
    def __setitem__(self, key, value):
        for _ in (): pass
        if key in ("__module__", "__static_attributes__"):
            log.append("module" if key == "__module__" else "static")
        if key == "m":
            log.append("def")
        super().__setitem__(key, value)
    def __delitem__(self, key):
        for _ in (): pass
        log.append("del")
        super().__delitem__(key)

class Prepare(Meta):
    @classmethod
    def __prepare__(mcls, name, bases, **kw):
        log.append("prepare")
        return Logged() if logged else {}

class Hook:
    def __init_subclass__(cls, **kw):
        log.append("init_subclass" + "".join(" " + k for k in kw))

class Plain:
    pass

class Entries:
    def __init__(self, base):
        self.base = base
    def __mro_entries__(self, bases):
        log.append("mro_entries")
        return (self.base,)

def deco(cls):
    log.append("decorate")
    return cls
'''


def source(p):
    base = "Hook" if p["subclass_hook"] else "Plain"
    if p["call"]:
        meta = {"none": "type", "meta": "Meta", "prepare": "Prepare", "init": "InitOnly"}[p["meta"]]
        lines = ["def body():", "    log.append('body')" if p["calls"] else "    pass",
                 "    return {'n': 1%s}" % "".join(", %r: D()" % name for name in "ab"[:p["set_names"]])]
        made = "%s('C', (%s,), body()%s)" % (meta, base, ", flag=1" if p["flag"] else "")
        lines.append("C = %s" % ("deco(%s)" % made if p["deco"] else made))
        return "\n".join(lines) + "\n"
    arguments = ["Entries(%s)" % base if p["entries"] else base]
    if p["meta"] != "none":
        arguments.append("metaclass=" + {"meta": "Meta", "prepare": "Prepare", "init": "InitOnly"}[p["meta"]])
    if p["flag"]:
        arguments.append("flag=1")
    lines = ["@deco"] if p["deco"] else []
    lines.append("class C%s(%s):" % ("[T]" if p["generic"] else "", ", ".join(arguments)))
    if p["annotated"]:
        lines.append("    x: int = 0")
    lines.append("    log.append('body')" if p["calls"] else "    n = 1")
    lines += ["    %s = D()" % name for name in "ab"[:p["set_names"]]]
    if p["logged"]:
        lines += ["    def m(self): pass", "    del m"]
    return "\n".join(lines) + "\n"


def outcome(p):
    namespace = {"log": [], "logged": p["logged"]}
    exec(HOOKS, namespace)
    namespace["log"].clear()
    try:
        exec(source(p), namespace)
    except TypeError:
        return (tuple(namespace["log"]), "TypeError")
    return (tuple(namespace["log"]), "ok")


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
