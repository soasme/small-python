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

class Prepare(Meta):
    @classmethod
    def __prepare__(mcls, name, bases, **kw):
        log.append("prepare")
        return {}

class Hook:
    def __init_subclass__(cls, **kw):
        log.append("init_subclass" + "".join(" " + k for k in kw))

class Plain:
    pass

def deco(cls):
    log.append("decorate")
    return cls
'''


def source(p):
    arguments = ["Hook" if p["subclass_hook"] else "Plain"]
    if p["meta"] != "none":
        arguments.append("metaclass=" + ("Meta" if p["meta"] == "meta" else "Prepare"))
    if p["flag"]:
        arguments.append("flag=1")
    lines = ["@deco"] if p["deco"] else []
    lines.append("class C(%s):" % ", ".join(arguments))
    lines.append("    log.append('body')")
    lines += ["    %s = D()" % name for name in "ab"[:p["set_names"]]]
    return "\n".join(lines) + "\n"


def outcome(p):
    namespace = {"log": []}
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
