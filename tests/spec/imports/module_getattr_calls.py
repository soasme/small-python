# spec: PLS-315 17.2
# description: a module's attribute read finds its namespace's entry, then
# its type's attributes (object's methods such as __repr__, __eq__ and
# __init__, bound to the module), and only then calls the namespace's
# __getattr__ with the name, which may loop; getattr() with a default and
# hasattr() take its AttributeError as missing, and another exception
# propagates. A module without __getattr__ raises AttributeError naming
# it. Inside functions as at module level.
from harness import *
import harness

Module = type(harness)
log = []

def fallback(name):
    for _ in (): pass
    log.append(name)
    if name == "missing": raise AttributeError("no " + name)
    if name == "boom": raise KeyError(name)
    return name.upper()

m = Module("m")
m.__getattr__ = fallback
m.real = 5

def reads():
    out = [m.real, m.abc, getattr(m, "xyz"), hasattr(m, "missing"), getattr(m, "missing", "default"),
           type(m.__repr__).__name__, m.__eq__(m), m.__init__ is not None, m.__name__, m.__dict__["real"]]
    try: m.missing
    except AttributeError as e: out.append(str(e))
    try: m.boom
    except KeyError as e: out.append(e.args)
    return out

expected = [5, "ABC", "XYZ", False, "default", "method-wrapper", True, True, "m", 5, "no missing", ("boom",)]
assert_eq(reads(), expected)
assert_eq(log, ["abc", "xyz", "missing", "missing", "missing", "boom"])
log.clear()
assert_eq((m.top, log), ("TOP", ["top"]))

plain = Module("plain")
assert_eq((type(plain.__repr__).__name__, hasattr(plain, "nothing"), plain.__eq__(plain)), ("method-wrapper", False, True))
assert_raises(AttributeError, lambda: plain.nothing)
try: plain.nothing
except AttributeError as e: assert_eq(str(e), "module 'plain' has no attribute 'nothing'")

# A native __getattr__ answers too, and a format field's read calls either.
module_type = type(__build_class__.__self__)
native_module = module_type("native")
native_module.__getattr__ = {"x": 1}.get
python_module = module_type("python")
def module_missing(name): return "got " + name
python_module.__getattr__ = module_missing
assert_eq([native_module.x, native_module.y, "{0.z}".format(python_module), "{0.x}".format(native_module), getattr(python_module, "w")],
          [1, None, "got z", "1", "got w"])
