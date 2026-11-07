# spec: PLS-315 7.5.3, 13.3.2
# description: An item of a list, tuple, str, bytes, bytearray or range at
# an instance calls the instance's Python __index__ once, the item that of
# its int; a result that is not an int is a TypeError, as is a call that
# cannot bind, and an index out of range the sequence's IndexError. Methods
# that loop run in function statements as at module level.
from harness import *

log = []

class I:
    def __init__(self, v): self.v = v
    def __index__(self):
        for _ in range(2): pass
        log.append(self.v)
        return self.v

class Wrong:
    def __index__(self):
        for _ in range(2): pass
        return "x"

class Failing:
    def __index__(self):
        for _ in range(2): pass
        raise KeyError("failing")

class Arity:
    def __index__(self, extra):
        for _ in range(2): pass
        return 0

def items():
    del log[:]
    l, t = [10, 20, 30], (1, 2, 3)
    out = [l[I(1)], t[I(-1)], "abc"[I(2)], b"xyz"[I(0)], bytearray(b"q")[I(0)], range(5)[I(3)], [l][I(0)][I(2)]]
    for key in (Wrong(), Failing(), Arity(), I(9)):
        try: l[key]
        except Exception as e: out.append((type(e).__name__, str(e)))
    out.append(list(log))
    return out

expected = [20, 3, "c", 120, 113, 3, 30, ("TypeError", "Wrong.__index__() must return an int, not str"),
            ("KeyError", "'failing'"), ("TypeError", "Arity.__index__() missing 1 required positional argument: 'extra'"),
            ("IndexError", "list index out of range"), [1, -1, 2, 0, 0, 3, 0, 2, 9]]
assert_eq(items(), expected)
assert_eq(items(), expected)
assert_eq([7, 8][I(1)], 8)
