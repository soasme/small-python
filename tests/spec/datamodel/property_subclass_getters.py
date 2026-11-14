# spec: PLS-315 7.3.5, 20.5
# description: reading an instance attribute that is an instance of a
# property subclass not defining __get__ calls property.__get__, which calls
# the getter, a Python function that may loop; an AttributeError from it
# falls back to the class's __getattr__, and a missing getter raises
# AttributeError, which also falls back; getattr() reads it alike. A
# subclass defining __get__ calls its own. Inside functions as at module
# level.
from harness import *

log = []

class P(property): pass
class Q(property):
    def __get__(self, obj, owner=None):
        log.append("own")
        return super().__get__(obj, owner)

class C:
    @P
    def p(self):
        for _ in (): pass
        log.append("p")
        return 1
    @P
    def bad(self):
        for _ in (): pass
        raise AttributeError("bad")
    @Q
    def q(self):
        log.append("q")
        return 2
    none = P()
    def __getattr__(self, name):
        log.append(("getattr", name))
        return name

class N:
    @P
    def fails(self):
        for _ in (): pass
        raise KeyError("fails")
    none = P()

def reads():
    o = C()
    out = [o.p, getattr(o, "p"), o.bad, o.q, o.none, C.p is C.__dict__["p"]]
    try: N().fails
    except KeyError as e: out.append(e.args)
    try: N().none
    except AttributeError as e: out.append(str(e))
    return out, log[:]

assert_eq(reads(), ([1, 1, "bad", 2, "none", True, ("fails",), "property 'none' of 'N' object has no getter"],
                    ["p", "p", ("getattr", "bad"), "own", "q", ("getattr", "none")]))
