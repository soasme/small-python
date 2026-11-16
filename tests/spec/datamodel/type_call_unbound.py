# spec: PLS-315 10.2.1, 20.2.5
# description: type.__call__ called unbound, type.__call__(cls, ...), in
# a metaclass's Python __call__ or elsewhere, with positional, starred or
# keyword arguments, or through another name, runs the class's Python
# __new__, then its __init__, each of which may loop, with the other
# arguments, without the metaclass's __call__, and returns the instance.
# An __init__ returning other than None raises TypeError, an error from
# either method propagates, and a first argument that is not a class
# raises TypeError. Inside functions as at module level.
from harness import *

log = []

class M(type):
    def __call__(cls, *a, **k):
        for _ in (): pass
        log.append(("call", cls.__name__))
        if k: return type.__call__(cls, *a, **k)
        if len(a) == 1: return type.__call__(cls, a[0])
        if len(a) == 2:
            call = type.__call__
            return call(cls, a[0], a[1])
        return type.__call__(cls, *a)

class P(metaclass=M):
    def __init__(self, *a, **k):
        for _ in (): pass
        log.append(("init", a, k))
        if a == (None,): raise LookupError("init")
        self.a = a

class Q(metaclass=M):
    def __new__(cls, *a, **k):
        for _ in (): pass
        log.append(("new", a, k))
        if a == (None,): raise LookupError("new")
        return super().__new__(cls)
    def __init__(self, *a, **k):
        for _ in (): pass
        log.append(("qinit", a, k))

class Plain:
    def __init__(self, v):
        for _ in (): pass
        log.append(("plain", v))
        self.v = v

class Bad(metaclass=M):
    def __init__(self, *a):
        return 3

def calls():
    return [P().a, P(1).a, P(1, 2).a, P(1, 2, 3).a, P(x=3).a, type(Q(1)).__name__, type(Q(1, 2)).__name__,
            type(Q(y=2)).__name__, type.__call__(P, 4).a, type.__call__(Plain, 5).v]

expected = [(), (1,), (1, 2), (1, 2, 3), (), "Q", "Q", "Q", (4,), 5]
expected_log = [("call", "P"), ("init", (), {}), ("call", "P"), ("init", (1,), {}), ("call", "P"), ("init", (1, 2), {}),
                ("call", "P"), ("init", (1, 2, 3), {}), ("call", "P"), ("init", (), {"x": 3}),
                ("call", "Q"), ("new", (1,), {}), ("qinit", (1,), {}), ("call", "Q"), ("new", (1, 2), {}), ("qinit", (1, 2), {}),
                ("call", "Q"), ("new", (), {"y": 2}), ("qinit", (), {"y": 2}), ("init", (4,), {}), ("plain", 5)]
assert_eq(calls(), expected)
assert_eq(log, expected_log)
log.clear()

assert_eq([P(1).a, type.__call__(P, 4).a, type.__call__(Plain, 5).v], [(1,), (4,), 5])
assert_eq(log, [("call", "P"), ("init", (1,), {}), ("init", (4,), {}), ("plain", 5)])
log.clear()

def errors():
    out = []
    for make in (lambda: P(None), lambda: Q(None), lambda: Bad(1), lambda: type.__call__(1)):
        try: make()
        except LookupError as e: out.append(e.args)
        except TypeError as e: out.append(str(e))
    return out

assert_eq(errors(), [("init",), ("new",), "__init__() should return None, not 'int'",
                     "descriptor '__call__' requires a 'type' object but received a 'int'"])

# Through an attribute of an object an expression gives, as a method call's
# callee.
class Holder: pass
holder = Holder()
holder.make = type.__call__
def held(): return holder
def through():
    log.clear()
    return [held().make(P, 6).a, held().make(Plain, 7).v]
assert_eq(through(), [(6,), 7])
assert_eq(log, [("init", (6,), {}), ("plain", 7)])
log.clear()
