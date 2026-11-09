# spec: PLS-315 19.3.13, 19.3.30, 7.6.2
# description: divmod() and pow() with no modulus or a None one are binary
# operations: the left operand's __divmod__ or __pow__ is called, which may
# loop, then on NotImplemented the right one's reflected method unless the
# classes are the same, and a right operand of a subclass that overrides
# the reflected method goes first; a number on the left declines to an
# instance's reflected method. Inside functions as at module level, both
# declining, the reflected method too, raises TypeError naming the
# function, a method's exceptions propagate, and a
# modulus is passed to __pow__.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Operand:
    def __init__(self, tag): self.tag = tag
    def __divmod__(self, other):
        spin()
        log.append(("divmod", self.tag))
        if self.tag == "bad": raise KeyError("divmod")
        return NotImplemented if self.tag == "no" else ("divmod", self.tag, other)
    def __rdivmod__(self, other):
        spin()
        log.append(("rdivmod", self.tag))
        return NotImplemented if self.tag == "rno" else ("rdivmod", self.tag, other)
    def __pow__(self, other, modulus=None):
        spin()
        log.append(("pow", self.tag, modulus))
        return NotImplemented if self.tag == "no" else ("pow", self.tag, other)
    def __rpow__(self, other, modulus=None):
        spin()
        log.append(("rpow", self.tag))
        return NotImplemented if self.tag == "rno" else ("rpow", self.tag, other)

class Derived(Operand):
    def __rdivmod__(self, other):
        spin()
        log.append(("derived", self.tag))
        return ("derived", self.tag)
    def __rpow__(self, other, modulus=None):
        spin()
        log.append(("rderived", self.tag))
        return ("rderived", self.tag)

class Other:
    def __rdivmod__(self, other):
        spin()
        log.append(("other", type(other).__name__))
        return "other"
    def __rpow__(self, other, modulus=None):
        spin()
        log.append(("rother", type(other).__name__))
        return "rother"

class Declines:
    def __rdivmod__(self, other):
        spin()
        log.append("declines rdivmod")
        return NotImplemented
    def __rpow__(self, other, modulus=None):
        spin()
        log.append("declines rpow")
        return NotImplemented

class Plain: pass
class Int(int): pass

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    out = [divmod(Operand("a"), 1), divmod(1, Operand("b")), divmod(1.5, Operand("c")), divmod(Int(7), Operand("d")),
           divmod(Operand("no"), Other()), divmod(Operand("a"), Derived("e")),
           error(lambda: divmod(Operand("no"), 1)), error(lambda: divmod(Operand("no"), Operand("x"))),
           error(lambda: divmod(Operand("no"), Int(3))), error(lambda: divmod(1, Operand("rno"))),
           error(lambda: divmod(Operand("bad"), 1)), error(lambda: divmod(Plain(), 1)), divmod(Int(7), 2),
           pow(Operand("a"), 2), pow(2, Operand("b")), pow(Operand("a"), 2, None), pow(Operand("no"), Other()),
           pow(Operand("a"), Derived("e")), pow(Operand("a"), 2, 5),
           error(lambda: pow(Operand("no"), 2)), error(lambda: pow(Operand("no"), Operand("x"))),
           error(lambda: pow(Plain(), 2)), error(lambda: divmod(Operand("no"), Declines())),
           error(lambda: pow(Operand("no"), Declines()))]
    out.append(list(log))
    return out

expected = [("divmod", "a", 1), ("rdivmod", "b", 1), ("rdivmod", "c", 1.5), ("rdivmod", "d", 7),
            "other", ("derived", "e"),
            ("TypeError", "unsupported operand type(s) for divmod(): 'Operand' and 'int'"),
            ("TypeError", "unsupported operand type(s) for divmod(): 'Operand' and 'Operand'"),
            ("TypeError", "unsupported operand type(s) for divmod(): 'Operand' and 'Int'"),
            ("TypeError", "unsupported operand type(s) for divmod(): 'int' and 'Operand'"),
            ("KeyError", "'divmod'"),
            ("TypeError", "unsupported operand type(s) for divmod(): 'Plain' and 'int'"), (3, 1),
            ("pow", "a", 2), ("rpow", "b", 2), ("pow", "a", 2), "rother", ("rderived", "e"), ("pow", "a", 2),
            ("TypeError", "unsupported operand type(s) for ** or pow(): 'Operand' and 'int'"),
            ("TypeError", "unsupported operand type(s) for ** or pow(): 'Operand' and 'Operand'"),
            ("TypeError", "unsupported operand type(s) for ** or pow(): 'Plain' and 'int'"),
            ("TypeError", "unsupported operand type(s) for divmod(): 'Operand' and 'Declines'"),
            ("TypeError", "unsupported operand type(s) for ** or pow(): 'Operand' and 'Declines'"),
            [("divmod", "a"), ("rdivmod", "b"), ("rdivmod", "c"), ("rdivmod", "d"),
             ("divmod", "no"), ("other", "Operand"), ("derived", "e"),
             ("divmod", "no"), ("divmod", "no"), ("divmod", "no"), ("rdivmod", "rno"), ("divmod", "bad"),
             ("pow", "a", None), ("rpow", "b"), ("pow", "a", None), ("pow", "no", None), ("rother", "Operand"),
             ("rderived", "e"), ("pow", "a", 5), ("pow", "no", None), ("pow", "no", None),
             ("divmod", "no"), "declines rdivmod", ("pow", "no", None), "declines rpow"]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
