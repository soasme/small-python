# spec: PLS-315 7.6.2
# description: when the left operand's class defines no method for a
# binary operator, the right operand's reflected method is called, a
# looping Python one too, whether the right operand is a plain instance,
# a subclass of the left's class or of a built-in type; or when the left
# operand is a class, whose type defines no method but | (a union of
# classes, which declines an instance); its
# NotImplemented gives the operator's TypeError and its exception
# propagates. Augmented assignment without an in-place method and sum()
# take the same reflected method. Inside functions as at module level.
from harness import *

log = []

class R:
    def __radd__(self, o):
        for _ in range(2): pass
        log.append(("R", type(o).__name__))
        return "R"

class N:
    def __radd__(self, o):
        for _ in range(2): pass
        return NotImplemented
    def __rsub__(self, o):
        for _ in range(2): pass
        raise KeyError("rsub")

class B(str):
    def __radd__(self, o):
        for _ in range(2): pass
        log.append(("B", type(o).__name__))
        return "B"

class P: pass

class Q(P):
    def __radd__(self, o):
        for _ in range(2): pass
        return "Q"

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def operations():
    del log[:]
    y = P()
    y += R()
    z = P
    z += R()
    out = [R() + B("a"), P() + Q(), P() + R(), error(lambda: P() + N()), error(lambda: P() - N()),
           error(lambda: P() + P()), error(lambda: R() + R()), y, sum([R()], P()), error(lambda: sum([N()], P())),
           int + R(), z, error(lambda: int | N()), error(lambda: P - N())]
    out.append(list(log))
    return out

expected = ["B", "Q", "R", ("TypeError", "unsupported operand type(s) for +: 'P' and 'N'"), ("KeyError", "'rsub'"),
            ("TypeError", "unsupported operand type(s) for +: 'P' and 'P'"),
            ("TypeError", "unsupported operand type(s) for +: 'R' and 'R'"), "R", "R",
            ("TypeError", "unsupported operand type(s) for +: 'P' and 'N'"),
            "R", "R", ("TypeError", "unsupported operand type(s) for |: 'type' and 'N'"), ("KeyError", "'rsub'"),
            [("R", "P"), ("R", "type"), ("B", "R"), ("R", "P"), ("R", "P"), ("R", "type")]]

def main():
    return operations()

assert_eq(main(), expected)
assert_eq(operations(), expected)
