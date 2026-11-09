# spec: PLS-315 26.3.2
# description: The union, intersection, difference and symmetric
# difference of two sets find equal elements by hash and then by ==, so an
# element's Python __eq__ is called with an element of equal hash from the
# other set; an exception from it propagates out of the operation, and the
# result has the left operand's type, inside functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class P:
    def __init__(self, v): self.v = v
    def __hash__(self): return self.v % 3
    def __eq__(self, other):
        spin()
        log.append(self.v)
        if self.v == 9 or getattr(other, "v", 0) == 9: raise KeyError(9)
        return isinstance(other, P) and self.v == other.v
    def __repr__(self): return "P%d" % self.v

def names(s):
    return type(s).__name__, sorted(map(repr, s))

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    a = {P(1), P(2), P(4), 7}
    b = {P(1), P(5), 3}
    out = [names(a | b), names(a & b), names(a - b), names(a ^ b), names(frozenset(a) & b),
           names(frozenset(b) - a), names({P(1)} | {P(1)})]
    out.append(bool(log))
    out += [error(lambda: {P(9)} | {P(0)}), error(lambda: {P(0)} & {P(9)}),
            error(lambda: {P(3)} - {P(9)}), error(lambda: {P(9)} ^ {P(6)})]
    if {P(1)} & {P(1)}: out.append("taken")
    return out

expected = [("set", ["3", "7", "P1", "P2", "P4", "P5"]), ("set", ["P1"]), ("set", ["7", "P2", "P4"]),
            ("set", ["3", "7", "P2", "P4", "P5"]), ("frozenset", ["P1"]), ("frozenset", ["3", "P5"]),
            ("set", ["P1"]), True, ("KeyError", "9"), ("KeyError", "9"), ("KeyError", "9"),
            ("KeyError", "9"), "taken"]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
