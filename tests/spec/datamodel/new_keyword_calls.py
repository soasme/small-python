# spec: PLS-315 10.2.1, 20.2.5
# description: a class call with keywords, or with ** or * arguments,
# calls the class's Python __new__ with the class, the positional
# arguments and the keywords, then, when it returns an instance of the
# class, the instance's __init__ with the same arguments and keywords; a
# result of another type is the call's value without __init__; a binding
# error of __new__ propagates; inside functions as at module level.
from harness import *

log = []

class N:
    def __new__(cls, *args, **kwargs):
        log.append(("new", cls.__name__, args, kwargs))
        return super().__new__(cls)
    def __init__(self, *args, **kwargs):
        log.append(("init", args, kwargs))

class Sub(N): pass

class Other:
    def __new__(cls, **kwargs):
        log.append(("other", kwargs))
        return 7
    def __init__(self, **kwargs):
        log.append("not called")

class Strict:
    def __new__(cls, *, key):
        return super().__new__(cls)

def calls(**extra):
    del log[:]
    made = [N(1, x=2), N(**extra), Sub(*[1, 2], y=3), Other(z=1), N(*(), **{})]
    return [type(v).__name__ for v in made], log[:]

expected = (["N", "N", "Sub", "int", "N"], [
    ("new", "N", (1,), {"x": 2}), ("init", (1,), {"x": 2}),
    ("new", "N", (), {"q": 5}), ("init", (), {"q": 5}),
    ("new", "Sub", (1, 2), {"y": 3}), ("init", (1, 2), {"y": 3}),
    ("other", {"z": 1}),
    ("new", "N", (), {}), ("init", (), {}),
])
assert_eq(calls(q=5), expected)

def errors():
    out = []
    try: Strict(other=1)
    except TypeError as e: out.append(str(e))
    try: Strict(**{"key": 1, "other": 2})
    except TypeError as e: out.append(str(e))
    out.append(type(Strict(key=1)).__name__)
    return out

assert_eq(errors(), ["Strict.__new__() got an unexpected keyword argument 'other'",
                     "Strict.__new__() got an unexpected keyword argument 'other'", "Strict"])
del log[:]
v = N(5, w=6)
assert_eq(log, [("new", "N", (5,), {"w": 6}), ("init", (5,), {"w": 6})])
