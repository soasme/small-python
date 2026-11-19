# spec: PLS-315 6.10.1 3.3.1
# description: A set, a frozenset, or an instance of a builtin's
# subclass that does not define a comparison, compares with an instance of an unrelated class by the
# builtin's method, which declines it: the other's reflected Python
# method answers, its value kept as given, and its NotImplemented leaves
# == and != to identity and an ordering to a TypeError naming both
# classes; an error it raises propagates. A subclass defining another
# comparison still declines this one. One whose own method declines
# leaves the reflected method, called once.
from harness import *

log = []

class I(int): pass
class F(float): pass
class S(str): pass
class B(bytes): pass
class T(tuple): pass
class L(list): pass
class D(dict): pass
class FS(frozenset): pass
class G(int):
    def __gt__(self, other): return "own gt"
class N(str):
    def __lt__(self, other):
        log.append("N.lt")
        return NotImplemented

class Other:
    def __init__(self, answer): self.answer = answer
    def __gt__(self, other):
        for _ in (): pass
        log.append(("gt", type(other).__name__))
        if self.answer == "raise": raise KeyError("gt")
        return self.answer
    def __eq__(self, other):
        for _ in (): pass
        log.append(("eq", type(other).__name__))
        return self.answer
    __hash__ = None

def attempt(f):
    try:
        return f()
    except (TypeError, KeyError) as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    out = []
    for x in (I(1), F(1.5), S("a"), B(b"a"), T((1,)), L([1]), G(2), N("n"), {1}, frozenset(), FS()):
        out.append(attempt(lambda: x < Other(("lt", 1))))
        out.append(attempt(lambda: x < Other(NotImplemented)))
    o = Other(NotImplemented)
    out += [attempt(lambda: I(1) == Other("eq")), attempt(lambda: D() != Other(0)), attempt(lambda: I(1) == o),
            attempt(lambda: S("a") != o), attempt(lambda: B(b"") < Other("raise")), list(log)]
    return out

def n(cls): return "'<' not supported between instances of '%s' and 'Other'" % cls

expected = [
    ("lt", 1), ("TypeError", n("I")), ("lt", 1), ("TypeError", n("F")), ("lt", 1), ("TypeError", n("S")),
    ("lt", 1), ("TypeError", n("B")), ("lt", 1), ("TypeError", n("T")), ("lt", 1), ("TypeError", n("L")),
    ("lt", 1), ("TypeError", n("G")), ("lt", 1), ("TypeError", n("N")),
    ("lt", 1), ("TypeError", n("set")), ("lt", 1), ("TypeError", n("frozenset")), ("lt", 1), ("TypeError", n("FS")),
    "eq", True, False, True, ("KeyError", "'gt'"),
    [("gt", "I"), ("gt", "I"), ("gt", "F"), ("gt", "F"), ("gt", "S"), ("gt", "S"), ("gt", "B"), ("gt", "B"),
     ("gt", "T"), ("gt", "T"), ("gt", "L"), ("gt", "L"), ("gt", "G"), ("gt", "G"),
     "N.lt", ("gt", "N"), "N.lt", ("gt", "N"),
     ("gt", "set"), ("gt", "set"), ("gt", "frozenset"), ("gt", "frozenset"), ("gt", "FS"), ("gt", "FS"),
     ("eq", "I"), ("eq", "D"), ("eq", "I"), ("eq", "S"), ("gt", "B")],
]

assert_eq(results(), expected)
def main(): return results()
assert_eq(main(), expected)
