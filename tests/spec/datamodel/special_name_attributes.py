# spec: PLS-315 7.3.4, 7.3.5
# description: Reading a special name off an instance follows
# GenericGetAttr like any other name, repeatedly at one site: the
# instance's own entry before its class's method, a class __getattribute__
# or __getattr__ as for other names, and a class change seen at once,
# down to object's own method.
from harness import *

class P:
    def __init__(self, v=0): self.v = v
    def __lt__(self, o): return "lt"
    def __class__(self): return "fn-class"
class Q(P):
    def __getattribute__(self, name):
        if name == "__lt__": return lambda o: "hooked"
        return object.__getattribute__(self, name)
class R(P):
    def __getattr__(self, name): return "fallback:" + name

def reads():
    out = []
    for _ in range(2):
        p = P(1)
        out.append(p.__lt__(p))
        p.__dict__["__lt__"] = lambda o: "own"
        out += [p.__lt__(p), p < p, type(p.__class__).__name__]
        out += [Q().__lt__(1), R().__lt__(1), R().__missing__]
        p.__init__(5)
        out += [p.v, p.__dict__ is p.__dict__, p.__module__]
        try:
            p.__nothere__
        except AttributeError as e:
            out.append(str(e))
    return out

once = ["lt", "own", "lt", "method", "hooked", "lt", "fallback:__missing__", 5, True, "__main__",
        "'P' object has no attribute '__nothere__'"]
assert_eq(reads(), once + once)
def first(p): return p.__lt__(p)
assert_eq(first(P()), "lt")
P.__lt__ = lambda self, o: "replaced"
assert_eq(first(P()), "replaced")
del P.__lt__
assert_eq(first(P()), NotImplemented)
