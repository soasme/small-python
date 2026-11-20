# spec: PLS-315 17.2, 19.3.12
# description: dir() of an instance of a module subclass reads its
# __dict__, which a property of the subclass may give: the property's
# Python getter, which may loop, runs once; a dict it returns gives its
# sorted keys, or what its own __dir__ entry returns, sorted; another value
# raises TypeError, and the getter's exception propagates.
from harness import *

log = []
ModuleType = type(__import__("builtins"))
class M(ModuleType):
    pass
def mk(kind):
    def get(self):
        for _ in (): pass
        log.append("get")
        if kind == "raise": raise KeyError("k")
        if kind == "str": return "Not a dict!"
        return {"b": 1, "a": 2}
    return type("M2", (M,), {"__dict__": property(get)})("m2")
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def listing(self):
    log.append("get")
    return {"q": 1, "__dir__": lambda: ["y", "x"]}

def results():
    out = []
    for kind in ("dict", "str", "raise"):
        x = mk(kind)
        out.append((run(lambda: [n for n in dir(x) if not n.startswith("__")]), run(lambda: len(dir(x)) > 0)))
    m = M("plain"); m.z = 1
    out.append(run(lambda: [n for n in dir(m) if not n.startswith("__")]))
    out.append(run(lambda: dir(type("M3", (M,), {"__dict__": property(listing)})("m3"))))
    out.append(run(lambda: dir(type("M4", (M,), {"__dict__": property(lambda self: {1: 2, "a": 3})})("m4"))))
    return out

not_dict = ("TypeError", "<module>.__dict__ is not a dictionary")
expected = [((["a", "b"], ["get"]), (True, ["get"])), ((not_dict, ["get"]), (not_dict, ["get"])),
            ((("KeyError", "'k'"), ["get"]), (("KeyError", "'k'"), ["get"])), (["z"], []), (["x", "y"], ["get"]),
            (("TypeError", "'<' not supported between instances of 'str' and 'int'"), [])]
assert_eq(results(), expected)
