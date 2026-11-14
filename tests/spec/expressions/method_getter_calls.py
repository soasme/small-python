# spec: PLS-315 13.3.1, 13.3.4, 7.3.4, 7.3.5
# description: a method call o.m(args) whose attribute is read by a
# Python property getter, descriptor __get__, __getattribute__, or a
# __getattr__ after an AttributeError, each of which may loop, reads the
# attribute first, then evaluates the arguments, then calls the value with
# them; an error from the read propagates, AttributeError only after
# __getattr__ when there is one, and a NameError of an argument follows
# the read. Calls on a class whose metaclass has a property, with
# arguments that are names, constants, subscripts or other calls, and
# with up to eight arguments; the value may be a class, whose __init__
# runs and must return None. Inside functions as at module level.
from harness import *

log = []

class D:
    def __get__(self, obj, owner):
        for _ in (): pass
        log.append("dget")
        return lambda *a: ("d", a)

class P:
    d = D()
    @property
    def f(self):
        for _ in (): pass
        log.append("get")
        return lambda x: x + 1
    @property
    def bad(self):
        for _ in (): pass
        raise LookupError("bad")
    @property
    def missing(self):
        for _ in (): pass
        log.append("missing")
        raise AttributeError("missing")
    def __getattr__(self, name):
        for _ in (): pass
        log.append(name)
        if name == "gone": raise AttributeError(name)
        return lambda *a: (name, a)

class G:
    def __getattribute__(self, name):
        for _ in (): pass
        log.append("ga")
        if name == "no": raise AttributeError(name)
        return lambda x: x - 1

class Meta(type):
    @property
    def make(cls):
        for _ in (): pass
        log.append("make")
        return lambda *a: (cls.__name__, a)

class K(metaclass=Meta): pass

class Plain:
    @property
    def f(self):
        for _ in (): pass
        log.append("plain")
        return P

def args(*a):
    log.append("args")
    return a

def calls():
    p = P(); g = G(); k = 5; t = [7, 8]
    out = [p.f(1), p.f(k), p.f(t[0]), p.h(3), p.missing(4), g.x(k)]
    out.append(p.d(1, 2, 3, 4, 5, 6, 7, 8))
    out.append(p.h(*args(1)))
    out.append(p.f(len(t)))
    out.append(K.make(k, 2))
    out.append(type(Plain().f()).__name__)
    return out

expected = [2, 6, 8, ("h", (3,)), ("missing", (4,)), 4,
            ("d", (1, 2, 3, 4, 5, 6, 7, 8)), ("h", (1,)), 3, ("K", (5, 2)), "P"]
expected_log = ["get", "get", "get", "h", "missing", "missing", "ga", "dget",
                "h", "args", "get", "make", "plain"]
assert_eq(calls(), expected)
assert_eq(log, expected_log)
log.clear()

p = P(); g = G(); k = 5; t = [7, 8]
assert_eq([p.f(1), p.f(k), p.f(t[0]), p.h(3), p.missing(4), g.x(k)], expected[:6])
assert_eq(log, expected_log[:7])
log.clear()

def errors():
    p = P(); g = G()
    out = []
    try: p.bad(1)
    except LookupError as e: out.append(e.args)
    try: p.gone(1)
    except AttributeError as e: out.append(e.args)
    try: g.no(1)
    except AttributeError as e: out.append(e.args)
    try: p.f(undefined_name)
    except NameError as e: out.append("name")
    try: p.f(1, 2)
    except TypeError as e: out.append("type")
    return out

assert_eq(errors(), [("bad",), ("gone",), ("no",), "name", "type"])
assert_eq(log, ["gone", "ga", "get", "get"])

# The value read may be a class, whose call makes an instance and runs its
# __init__, which must return None.
class Made:
    def __init__(self, *a):
        for _ in (): pass
        log.append("init")
        self.a = a

class Items(list):
    def __init__(self, *a):
        for _ in (): pass
        log.append("items")
        super().__init__(a)

class Wrong:
    def __init__(self):
        for _ in (): pass
        return 1

class Maker:
    @property
    def made(self):
        for _ in (): pass
        return Made
    def __getattr__(self, name):
        for _ in (): pass
        return Items if name == "items" else Wrong

def classes():
    log.clear()
    m = Maker(); k = 4
    out = [m.made(k, 5).a, m.items(1, k), type(m.items()).__name__]
    try: m.wrong()
    except TypeError as e: out.append(str(e))
    return out

assert_eq(classes(), [(4, 5), [1, 4], "Items", "__init__() should return None, not 'int'"])
assert_eq(log, ["init", "items", "items"])
