# spec: PLS-315 7.2.4, 13.10
# description: x != y of instances whose classes define a Python __eq__
# and inherit object's __ne__ calls that __eq__ once and inverts its
# truth, whatever it returns; a NotImplemented goes on with the other
# operand's reflected method, then identity, and an exception propagates.
# x's own __eq__ comes first, a subclass operand's first, and a builtin
# operand's or a number's last; an __eq__ that cannot take the operands is
# a TypeError, in a lone test, an if, a chain and a not,
# inside functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class E:
    def __init__(self, v): self.v = v
    def __eq__(self, other):
        spin()
        log.append(("eq", self.v, type(other).__name__))
        if self.v == "raise": raise KeyError("eq")
        return NotImplemented if self.v == "decline" else self.v

class Sub(E):
    def __eq__(self, other):
        spin()
        log.append(("sub", self.v, type(other).__name__))
        return self.v

class Ne:
    def __ne__(self, other):
        spin()
        log.append(("ne", type(other).__name__))
        return "ne"

class Bare:
    pass

class Unary:
    def __eq__(self):
        spin()
        return True

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    yes, empty, d = E(True), E(""), E("decline")
    held = [yes, E(0), Sub(1), Ne()]
    flag = yes != empty
    out = [flag, empty != yes, E("x") != 3, "a" != yes, 1 != empty, None != d, d != d, d != E("decline"),
           d != held[3], held[3] != d, yes != held[2], held[0] != held[1], Bare() != d, error(lambda: E("raise") != 1),
           error(lambda: "a" != E("raise")), error(lambda: d != Unary())]
    if empty != yes: out.append("taken")
    out.append(not (yes != 1))
    out.append(yes != empty != d)
    out.append(list(log))
    return out

expected = [False, True, False, False, True, True, False, True, "ne", "ne", False, False, True, ("KeyError", "'eq'"),
            ("KeyError", "'eq'"),
            ("TypeError", "Unary.__eq__() takes 1 positional argument but 2 were given"), "taken", True, False,
            [("eq", True, "E"), ("eq", "", "E"), ("eq", "x", "int"), ("eq", True, "str"), ("eq", "", "int"),
             ("eq", "decline", "NoneType"), ("eq", "decline", "E"), ("eq", "decline", "E"), ("eq", "decline", "E"),
             ("eq", "decline", "E"), ("eq", "decline", "Ne"), ("ne", "E"), ("ne", "E"), ("sub", 1, "E"), ("eq", True, "E"),
             ("eq", "decline", "Bare"), ("eq", "raise", "int"), ("eq", "raise", "str"), ("eq", "decline", "Unary"), ("eq", "", "E"), ("eq", True, "int"),
             ("eq", True, "E")]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
