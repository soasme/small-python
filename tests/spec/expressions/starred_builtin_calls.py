# spec: PLS-315 13.3.4, 19.3.3, 19.3.16, 19.3.32, 23.1.1
# description: a call to a builtin with starred arguments unpacks them, then
# calls the builtin as a call with those positional arguments does: any and
# all test each item by its Python __bool__ in turn, stopping at the first
# deciding one; str, repr and format call the argument's Python __str__,
# __repr__ or __format__, each of which may loop, and an error from any of
# them propagates. Inside functions as at module level.
from harness import *

log = []

class B:
    def __init__(self, v): self.v = v
    def __bool__(self):
        for _ in (): pass
        log.append(self.v)
        return self.v

class W:
    def __str__(self):
        for _ in (): pass
        log.append("str")
        return "s"
    def __repr__(self):
        for _ in (): pass
        log.append("repr")
        return "r"
    def __format__(self, spec):
        for _ in (): pass
        log.append(("format", spec))
        return "f" + spec

def calls():
    out = []
    out.append((any(*[[B(False), B(True), B(True)]]), log[:])); log.clear()
    out.append((all(*([B(True), B(False), B(True)],)), log[:])); log.clear()
    args = [W()]
    out.append((str(*args), repr(*args), format(*args), format(*[W(), "x"]), log[:])); log.clear()
    return out

assert_eq(calls(), [
    (True, [False, True]),
    (False, [True, False]),
    ("s", "r", "f", "fx", ["str", "repr", ("format", ""), ("format", "x")]),
])

class Bad:
    def __bool__(self):
        for _ in (): pass
        raise LookupError("bool")
    def __str__(self):
        for _ in (): pass
        raise LookupError("str")

def errors():
    out = []
    try: any(*[[Bad()]])
    except LookupError as e: out.append(e.args)
    try: str(*[Bad()])
    except LookupError as e: out.append(e.args)
    return out

assert_eq(errors(), [("bool",), ("str",)])
