# Replays ClassCreation.tla: each case runs the spec's class statement with
# logging hooks and compares the log with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

HOOKS = '''
class D:
    def __set_name__(self, owner, name):
        log.append("set_name " + name)

class S:
    __set_name__ = staticmethod(lambda owner, name: log.append("set_name " + name))

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

class MroOnly(type):
    def mro(cls):
        for _ in (): pass
        log.append("mro")
        return type.mro(cls)

class Logged(dict):
    def __setitem__(self, key, value):
        for _ in (): pass
        if key in ("__module__", "__static_attributes__"):
            log.append("module" if key == "__module__" else "static")
        if key == "m":
            log.append("def")
        if key == "j":
            log.append("chain")
        if key == "e":
            log.append("handler" if value is None else "caught")
        if key in ("s", "t"):
            log.append("plain")
        super().__setitem__(key, value)
    def __getitem__(self, key):
        for _ in (): pass
        if key == "m":
            log.append("load")
        return super().__getitem__(key)
    def __delitem__(self, key):
        for _ in (): pass
        log.append("del")
        super().__delitem__(key)

def prepare(name, bases, **kw):
    log.append("prepare")
    return Logged() if logged else {}

class PrepareGet:
    def __get__(self, instance, owner):
        for _ in (): pass
        log.append("prepare_get")
        return prepare

class Prepare(Meta):
    __prepare__ = PrepareGet()

class Hook:
    def __init_subclass__(cls, **kw):
        log.append("init_subclass" + "".join(" " + k for k in kw))

class Plain:
    pass

class Adds:
    def __add__(self, other):
        for _ in (): pass
        log.append("add")
        return other

class Entries:
    def __init__(self, base):
        for _ in (): pass
        log.append("base")
        self.base = base
    def __getattribute__(self, name):
        for _ in (): pass
        return object.__getattribute__(self, name)
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
        meta = {"none": "type", "meta": "Meta", "prepare": "Prepare", "init": "InitOnly", "mro": "MroOnly"}[p["meta"]]
        lines = ["def body():", "    log.append('body')" if p["calls"] else "    pass",
                 "    return {'n': 1%s}" % "".join(", %r: %s()" % (name, kind) for name, kind in list(zip("ab", "DS"))[:p["set_names"]])]
        made = "%s('C', (%s,), body()%s)" % (meta, base, ", flag=1" if p["flag"] else "")
        lines.append("C = %s" % ("deco(%s)" % made if p["deco"] else made))
        return "\n".join(lines) + "\n"
    arguments = ["Entries(%s)" % base if p["entries"] else base]
    if p["meta"] != "none":
        arguments.append("metaclass=" + {"meta": "Meta", "prepare": "Prepare", "init": "InitOnly", "mro": "MroOnly"}[p["meta"]])
    if p["flag"]:
        arguments.append("flag=1")
    lines = ["@deco"] if p["deco"] else []
    lines.append("class C%s(%s):" % ("[T]" if p["generic"] else "", ", ".join(arguments)))
    if p["annotated"]:
        lines.append("    x: int = 0")
    lines.append("    log.append('body')" if p["calls"] else "    n = Adds() + 1")
    lines += ["    %s = %s()" % (name, kind) for name, kind in list(zip("ab", "DS"))[:p["set_names"]]]
    if p["logged"]:
        lines += ["    def m(self): pass", "    m", "    del m", "    k = j = 1", "    del k, j",
                  "    try: 1/0", "    except ZeroDivisionError as e: pass",
                  "    try:", "        try: 1/0", "        except ZeroDivisionError as e: raise KeyError", "    except KeyError: pass",
                  "    s = 1", "    t = 2"]
    return "\n".join(lines) + "\n"


def outcome(p):
    namespace = {"log": [], "logged": p["logged"]}
    exec(HOOKS, namespace)
    namespace["log"].clear()
    if p["builder"]:
        # The statement's __build_class__ is Python, calling the builtin one.
        builtin = __build_class__
        def builder(func, name, *bases, **kwds):
            for _ in (): pass
            return builtin(func, name, *bases, **kwds)
        table = __builtins__ if isinstance(__builtins__, dict) else vars(__builtins__)
        namespace["__builtins__"] = dict(table, __build_class__=builder)
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
