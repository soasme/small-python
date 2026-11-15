# spec: PLS-315 10.2.1, 20.2.5
# description: a metaclass's Python __call__ that calls super().__call__,
# with no arguments, positional ones, starred ones or keywords, runs
# type.__call__: the class's Python __new__, then its __init__, each of
# which may loop, with the arguments; a builtin subclass's Python
# __init__ after the builtin made it; and returns the instance. An
# __init__ returning other than None raises TypeError, non-string keyword
# names TypeError, and an error from either method propagates. Inside
# functions as at module level.
from harness import *

log = []

class M(type):
    def __call__(cls, *a, **k):
        for _ in (): pass
        log.append(("call", cls.__name__))
        if k: return super().__call__(*a, **k)
        if len(a) == 1: return super().__call__(a[0])
        if len(a) == 2: return super().__call__(a[0], a[1])
        if len(a) == 3: return super().__call__(*a)
        return super().__call__()

class P(metaclass=M):
    def __init__(self, *a, **k):
        for _ in (): pass
        log.append(("init", a, k))
        if a == (None,): raise LookupError("init")

class Q(metaclass=M):
    def __new__(cls, *a, **k):
        for _ in (): pass
        log.append(("new", a, k))
        if a == (None,): raise LookupError("new")
        return super().__new__(cls)
    def __init__(self, *a, **k):
        for _ in (): pass
        log.append(("qinit", a, k))

class L(list, metaclass=M):
    def __init__(self, *a):
        for _ in (): pass
        log.append(("linit", a))
        super().__init__(*a)

class Bad(metaclass=M):
    def __init__(self, *a):
        return 3

def calls():
    out = [type(P()).__name__, type(P(1)).__name__, type(P(1, 2)).__name__, type(P(1, 2, 3)).__name__,
           type(P(x=3)).__name__, type(Q()).__name__, type(Q(1)).__name__, type(Q(y=2)).__name__, L([4]), L()]
    return out

expected = ["P", "P", "P", "P", "P", "Q", "Q", "Q", [4], []]
expected_log = [("call", "P"), ("init", (), {}), ("call", "P"), ("init", (1,), {}), ("call", "P"), ("init", (1, 2), {}),
                ("call", "P"), ("init", (1, 2, 3), {}), ("call", "P"), ("init", (), {"x": 3}),
                ("call", "Q"), ("new", (), {}), ("qinit", (), {}), ("call", "Q"), ("new", (1,), {}), ("qinit", (1,), {}),
                ("call", "Q"), ("new", (), {"y": 2}), ("qinit", (), {"y": 2}),
                ("call", "L"), ("linit", ([4],)), ("call", "L"), ("linit", ())]
assert_eq(calls(), expected)
assert_eq(log, expected_log)
log.clear()

assert_eq([type(P(1, 2)).__name__, type(Q(1)).__name__], ["P", "Q"])
assert_eq(log, [("call", "P"), ("init", (1, 2), {}), ("call", "Q"), ("new", (1,), {}), ("qinit", (1,), {})])
log.clear()

def errors():
    out = []
    for f in (lambda: Bad(), lambda: Bad(1), lambda: P(**{1: 2}), lambda: P(None), lambda: Q(None)):
        try: f()
        except (TypeError, LookupError) as e: out.append((type(e).__name__, str(e)))
    return out

assert_eq(errors(), [("TypeError", "__init__() should return None, not 'int'"), ("TypeError", "__init__() should return None, not 'int'"),
                     ("TypeError", "keywords must be strings"), ("LookupError", "init"), ("LookupError", "new")])
assert_eq(log, [("call", "Bad"), ("call", "Bad"), ("call", "P"), ("init", (None,), {}), ("call", "Q"), ("new", (None,), {})])
