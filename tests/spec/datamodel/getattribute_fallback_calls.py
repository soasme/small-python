# spec: PLS-315 7.3.4
# description: An attribute reference on an instance whose class defines
# both a Python __getattribute__ and a Python __getattr__, each of which
# may loop, calls __getattribute__ with the name, and on an AttributeError
# from it __getattr__, which was found before __getattribute__ ran; any
# other exception from either propagates, inherited methods behave alike,
# and a chain or a generator reads the same; inside functions as at
# module level.
from harness import *

log = []

def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class A:
    def __init__(self): object.__setattr__(self, "own", 1)
    def __getattribute__(self, name):
        spin(); log.append(("ga", name))
        if name == "boom": raise KeyError("ga")
        if name.startswith("miss"): raise AttributeError(name)
        return object.__getattribute__(self, name)
    def __getattr__(self, name):
        spin(); log.append(("gt", name))
        if name == "miss2": raise AttributeError("deep")
        if name == "miss3": raise ValueError("gt")
        return "fallback:" + name

class B(A): pass

class Removing:
    def __getattribute__(self, name):
        spin(); log.append("remove")
        del Removing.__getattr__
        raise AttributeError(name)
    def __getattr__(self, name):
        spin(); log.append("found"); return "found first"

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def reads():
    del log[:]
    a, b = A(), B()
    out = [a.own, a.miss, b.own, b.missing, error(lambda: a.boom), error(lambda: a.miss2), error(lambda: a.miss3),
           a.miss4.upper(), Removing().x]
    def gen():
        yield a.miss5
    out.append(list(gen()))
    out.append(list(log))
    return out

expected = [1, "fallback:miss", 1, "fallback:missing", ("KeyError", "'ga'"), ("AttributeError", "deep"), ("ValueError", "gt"),
            "FALLBACK:MISS4", "found first", ["fallback:miss5"],
            [("ga", "own"), ("ga", "miss"), ("gt", "miss"), ("ga", "own"), ("ga", "missing"), ("gt", "missing"), ("ga", "boom"),
             ("ga", "miss2"), ("gt", "miss2"), ("ga", "miss3"), ("gt", "miss3"), ("ga", "miss4"), ("gt", "miss4"),
             "remove", "found", ("ga", "miss5"), ("gt", "miss5")]]
assert_eq(reads(), expected)
Removing.__getattr__ = lambda self, name: (spin(), log.append("found"), "found first")[2]
assert_eq(reads(), expected)
a = A()
log.clear()
assert_eq([a.own, a.miss], [1, "fallback:miss"])
assert_eq(log, [("ga", "own"), ("ga", "miss"), ("gt", "miss")])
