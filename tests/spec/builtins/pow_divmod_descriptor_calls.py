# spec: PLS-315 19.3.13, 19.3.30, 7.6.2
# description: pow() with a modulus and divmod() read an operand's method
# through its class attribute's Python __get__, which may loop, given the
# operand and its class, then call what it returns with the other
# operands; a method it returns may decline with NotImplemented, and an
# AttributeError from __get__ leaves the method absent, inside functions
# as at module level.
from harness import *

log = []

class D:
    def __init__(self, tag): self.tag = tag
    def __get__(self, obj, cls):
        for _ in range(2): pass
        log.append(("get", self.tag, type(obj).__name__, cls.__name__))
        if self.tag == "attr": raise AttributeError("gone")
        if self.tag == "bad": raise LookupError("get")
        tag = self.tag
        def method(*args):
            log.append((tag,) + tuple(type(a).__name__ for a in args))
            return NotImplemented if tag == "no" else tag
        return method

class A:
    __divmod__ = D("dm")
    __pow__ = D("pw")
class B:
    __divmod__ = D("no")
    __rdivmod__ = D("rdm")
class C:
    __divmod__ = D("attr")
class E:
    __pow__ = D("bad")

def t(f):
    del log[:]
    try: r = f()
    except Exception as e: r = type(e).__name__ + ": " + str(e)
    return r, list(log)

def results():
    return [t(lambda: divmod(A(), 1)), t(lambda: pow(A(), 2, 3)), t(lambda: divmod(B(), B())), t(lambda: divmod(1, B())),
            t(lambda: divmod(C(), 1)), t(lambda: pow(E(), 1, 2))]

expected = [("dm", [("get", "dm", "A", "A"), ("dm", "int")]),
            ("pw", [("get", "pw", "A", "A"), ("pw", "int", "int")]),
            ("TypeError: unsupported operand type(s) for divmod(): 'B' and 'B'", [("get", "no", "B", "B"), ("no", "B")]),
            ("rdm", [("get", "rdm", "B", "B"), ("rdm", "int")]),
            ("TypeError: unsupported operand type(s) for divmod(): 'C' and 'int'", [("get", "attr", "C", "C")]),
            ("LookupError: get", [("get", "bad", "E", "E")])]
assert_eq(results(), expected)

def gen():
    yield results()
assert_eq(next(gen()), expected)
