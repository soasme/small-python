# spec: PLS-315 16.4.2, 16.1.2, 14.4, 14.7, 9.3.5
# description: a class body whose namespace's class has a Python
# __setitem__ and __delitem__, each of which may loop, binds each def,
# class and annotated assignment of a name by __setitem__, after the
# value is made, its defaults evaluated and decorators applied, also in
# if, for and try blocks; and deletes each name of del, in order, by
# __delitem__, any error of which becomes a NameError for the name. A
# global name is bound and deleted in the module. Inside functions as at
# module level.
from harness import *

log = []

class NS(dict):
    def __setitem__(self, k, v):
        for _ in (): pass
        if not k.startswith("__"): log.append(("set", k))
        super().__setitem__(k, v)
    def __delitem__(self, k):
        for _ in (): pass
        log.append(("del", k))
        if k == "gone": raise LookupError(k)
        super().__delitem__(k)

class Meta(type):
    @classmethod
    def __prepare__(m, n, b): return NS()

def deco(f):
    log.append("deco")
    return f

def default():
    log.append("default")
    return 1

g = 0

def run():
    class K(metaclass=Meta):
        global g
        @deco
        def f(self, a=default()): return a
        class Inner: pass
        z: int = 3
        if z:
            def h(self): pass
        for i in range(1):
            w: str = "w"
        try:
            def t(self): pass
        finally:
            del i
        a = b = 1
        del a, b
        g = 5
        del g
    return sorted(k for k in K.__dict__ if not k.startswith("__")), K().f()

expected = (["Inner", "f", "h", "t", "w", "z"], 1)
expected_log = ["default", "deco", ("set", "f"), ("set", "Inner"), ("set", "z"), ("set", "h"), ("set", "i"), ("set", "w"),
                ("set", "t"), ("del", "i"), ("set", "a"), ("set", "b"), ("del", "a"), ("del", "b")]
assert_eq(run(), expected)
assert_eq(log, expected_log)
assert_eq("g" in globals(), False)
log.clear()

class M(metaclass=Meta):
    def m(self): pass
    v: int = 2
    del v

assert_eq((sorted(k for k in M.__dict__ if not k.startswith("__")), log), (["m"], [("set", "m"), ("set", "v"), ("del", "v")]))

def errors():
    out = []
    try:
        class E(metaclass=Meta):
            gone = 1
            del gone
    except NameError as e: out.append((str(e), e.__context__))
    try:
        class F(metaclass=Meta):
            del missing
    except NameError as e: out.append(str(e))
    return out

assert_eq(errors(), [("name 'gone' is not defined", None), "name 'missing' is not defined"])
