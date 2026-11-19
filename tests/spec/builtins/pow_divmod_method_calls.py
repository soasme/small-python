# spec: PLS-315 19.3.13, 19.3.30, 7.6.2
# description: pow() with a modulus and divmod() call the operands' Python
# methods in binary order, a subclass's reflected method first, then the
# left one's direct method and the right one's reflected one, each of
# which may loop: the first result that is not NotImplemented is the
# call's, an exception propagates, and when all decline pow() and divmod()
# raise TypeError naming the operands' types. Given by keyword, of a class
# whose metaclass defines them, and inside generators as at module level.
from harness import *

log = []

class N:
    def __init__(self, tag): self.tag = tag
    def __pow__(self, other, modulus=None):
        for _ in range(2): pass
        log.append(("pow", self.tag, modulus))
        if self.tag == "bad": raise LookupError("pow")
        return NotImplemented if self.tag == "no" else ("pow", self.tag)
    def __rpow__(self, other, modulus=None):
        for _ in range(2): pass
        log.append(("rpow", self.tag, modulus))
        return NotImplemented if self.tag in ("no", "rno") else ("rpow", self.tag)
    def __divmod__(self, other):
        for _ in range(2): pass
        log.append(("divmod", self.tag))
        if self.tag == "bad": raise LookupError("divmod")
        return NotImplemented if self.tag == "no" else ("divmod", self.tag)
    def __rdivmod__(self, other):
        for _ in range(2): pass
        log.append(("rdivmod", self.tag))
        return NotImplemented if self.tag in ("no", "rno") else ("rdivmod", self.tag)

class Sub(N):
    def __rpow__(self, other, modulus=None):
        for _ in range(2): pass
        log.append(("sub rpow", self.tag, modulus))
        return ("sub rpow", self.tag)
    def __rdivmod__(self, other):
        for _ in range(2): pass
        log.append(("sub rdivmod", self.tag))
        return NotImplemented if self.tag == "rno" else ("sub rdivmod", self.tag)

class O:
    def __rpow__(self, other, modulus=None):
        for _ in range(2): pass
        log.append(("o rpow", modulus))
        return ("o rpow",)
    def __rdivmod__(self, other):
        for _ in range(2): pass
        log.append(("o rdivmod",))
        return ("o rdivmod",)

class Meta(type):
    def __divmod__(cls, other):
        for _ in range(2): pass
        return ("meta divmod", other)
    def __pow__(cls, other, modulus=None):
        for _ in range(2): pass
        return ("meta pow", other, modulus)

class M(metaclass=Meta): pass

def t(f):
    del log[:]
    try: r = f()
    except Exception as e: r = type(e).__name__ + ": " + str(e)
    return r, list(log)

def results():
    return [t(lambda: pow(N(1), 2, 5)), t(lambda: pow(N("no"), O(), 5)), t(lambda: pow(N(1), Sub(2), 5)),
            t(lambda: pow(N("no"), N("no"), 5)), t(lambda: pow(N("bad"), 2, 5)), t(lambda: pow(base=N(3), exp=2, mod=7)),
            t(lambda: divmod(N(1), 2)), t(lambda: divmod(2, N(3))), t(lambda: divmod(N("no"), O())), t(lambda: divmod(N(1), Sub("rno"))),
            t(lambda: divmod(N("no"), N("no"))), t(lambda: divmod(N("bad"), 1)), t(lambda: divmod(M, 3)), t(lambda: pow(M, 2, 3))]

expected = [(("pow", 1), [("pow", 1, 5)]), (("o rpow",), [("pow", "no", 5), ("o rpow", 5)]),
            (("sub rpow", 2), [("sub rpow", 2, 5)]),
            ("TypeError: unsupported operand type(s) for ** or pow(): 'N', 'N', 'int'", [("pow", "no", 5)]),
            ("LookupError: pow", [("pow", "bad", 5)]), (("pow", 3), [("pow", 3, 7)]),
            (("divmod", 1), [("divmod", 1)]), (("rdivmod", 3), [("rdivmod", 3)]),
            (("o rdivmod",), [("divmod", "no"), ("o rdivmod",)]), (("divmod", 1), [("sub rdivmod", "rno"), ("divmod", 1)]),
            ("TypeError: unsupported operand type(s) for divmod(): 'N' and 'N'", [("divmod", "no")]),
            ("LookupError: divmod", [("divmod", "bad")]), (("meta divmod", 3), []), (("meta pow", 2, 3), [])]

assert_eq(results(), expected)

def gen():
    yield results()
    yield divmod(N(5), 1)
assert_eq(list(gen()), [expected, ("divmod", 5)])
