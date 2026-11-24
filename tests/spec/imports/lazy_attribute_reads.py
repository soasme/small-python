# spec: PLS-315 17.5, 7.3.1, 21.1.4
# description: A module attribute bound to a lazy import object is reified
# by the attribute's read, getattr(), a method call on it and a str.format
# field, each calling the recorded __import__, a Python function that may
# loop, and rebinding the attribute; a missing name raises ImportError at
# the read; the module is not loaded before. str.format fields also read a module's Python __getattr__ and
# a class's Python __getattribute__.
from harness import *
import builtins

real = builtins.__import__
log = []
def hook(name, *args):
    for _ in range(2): pass
    log.append(name)
    return real(name, *args)

def holder(*names):
    host.module_cache().pop("spec_lar_value", None)
    h = type(builtins)("h")
    h.__dict__["__builtins__"] = {"__import__": hook, "__lazy_import__": builtins.__lazy_import__}
    exec("lazy from spec_lar_value import " + ", ".join(names), h.__dict__)
    return h

def read(how):
    h = holder("value", "f")
    del log[:]
    result = how(h)
    return result, type(h.__dict__["value"]).__name__, len(log)

class Got:
    def __getattribute__(self, name):
        for _ in range(2): pass
        return "got " + name
named = type(builtins)("named")
def module_getattr(name):
    for _ in range(2): pass
    return name.upper()
named.__getattr__ = module_getattr

def cases():
    missing = holder("nope")
    try:
        missing.nope
    except ImportError as e:
        failure = str(e).split(" (")[0]
    return [read(lambda h: h.value), read(lambda h: getattr(h, "value")), read(lambda h: h.f()),
            read(lambda h: "{0.value}".format(h)), read(lambda h: "{0.value}{0.value}".format(h)),
            "{0.x}|{0.y}".format(named, named), "{0.z}".format(Got()), failure,
            str(assert_raises(AttributeError, lambda: "{0.other}".format(holder("value"))))]
expected = [(5, "int", 1), (5, "int", 1), ("called", "lazy_import", 1), ("5", "int", 1), ("55", "int", 1),
            "X|Y", "got z", "cannot import name 'nope' from 'spec_lar_value'", "module 'h' has no attribute 'other'"]
assert_eq(cases(), expected)
def gen():
    yield cases()
assert_eq(next(gen()), expected)
