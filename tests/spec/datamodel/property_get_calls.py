# spec: PLS-315 20.5
# description: property.__get__ called for an object, unbound with the
# property first, bound to it, or reached through super() from a property
# subclass's own __get__, calls the getter, a Python function that may
# loop, with the object; its value is the call's and its error propagates;
# for None and an owner the property itself is the value, and with no
# getter AttributeError is raised. Inside functions as at module level.
from harness import *

log = []

class Q(property):
    def __get__(self, obj, owner=None):
        for _ in (): pass
        log.append("own")
        return ("q", super().__get__(obj, owner))

class C:
    @Q
    def q(self):
        for _ in (): pass
        log.append("get")
        return 2
    @property
    def p(self):
        for _ in (): pass
        log.append("p")
        return 3
    @property
    def bad(self):
        for _ in (): pass
        raise KeyError("bad")

def calls():
    c = C()
    p = C.__dict__["p"]
    out = [c.q, p.__get__(c), property.__get__(p, c, C), p.__get__(None, C) is p, super(Q, C.__dict__["q"]).__get__(c)]
    try: property.__get__(C.__dict__["bad"], c)
    except KeyError as e: out.append(e.args)
    try: Q(None).__get__(c)
    except AttributeError as e: out.append(str(e))
    out.append(log[:])
    return out

assert_eq(calls(), [("q", 2), 3, 3, True, 2, ("bad",), "property of 'C' object has no getter", ["own", "get", "p", "p", "get", "own"]])
