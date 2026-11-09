# spec: PLS-315 26.3.2
# description: The union, intersection, difference and symmetric
# difference of two sets, their augmented assignments, and the subset,
# superset and equality comparisons find equal elements by hash and then
# by ==, so an element's Python __eq__ is called with an element of equal
# hash from the other set; an exception from it propagates out of the
# operation. The result has the left operand's type; an augmented
# assignment updates a set in place and makes a new frozenset; a
# comparison is a bool, also in a test and a chain, inside functions as at
# module level.
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
        if 9 in (self.v, getattr(other, "v", 0)): raise KeyError(9)
        return isinstance(other, P) and self.v == other.v
    def __repr__(self): return "P%d" % self.v

def names(s):
    return type(s).__name__, sorted(map(repr, s))

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def updated():
    out = []
    for op in ("|=", "&=", "-=", "^="):
        a, b = {P(1), P(2), P(4), 7}, {P(1), P(5), 3}
        before = a
        if op == "|=": a |= b
        elif op == "&=": a &= b
        elif op == "-=": a -= b
        else: a ^= b
        out.append((names(a), a is before))
    a = {P(1), P(2)}
    a ^= a
    f = before = frozenset({P(1)})
    f |= {P(2)}
    out += [names(a), names(f), f is before]
    a = {P(9)}
    try:
        a |= {P(0)}
    except KeyError as e:
        out.append(("KeyError", str(e), names(a)))
    return out

expected_updated = [(("set", ["3", "7", "P1", "P2", "P4", "P5"]), True), (("set", ["P1"]), True),
                    (("set", ["7", "P2", "P4"]), True), (("set", ["3", "7", "P2", "P4", "P5"]), True),
                    ("set", []), ("frozenset", ["P1", "P2"]), False, ("KeyError", "9", ("set", ["P9"]))]

def compared():
    a, b, e, d = {P(1), P(2)}, {P(1), P(2), P(4)}, {P(1), P(2)}, {P(1), P(5)}
    out = [a <= b, a < b, b >= a, b > a, a == e, a != e, a == d, a != d, a < e, a <= e, b <= a, d <= b,
           frozenset(a) == e, a >= e, a > e, a <= b <= b, a == b]
    if d <= b: out.append("taken")
    if a < b < b | d: out.append("chain")
    out += [b > a == e, a < b < a, error(lambda: a == e != {P(0)} <= {P(9), P(3)})]
    out.append(error(lambda: {P(9)} == {P(0)}))
    out.append(error(lambda: {P(0)} <= {P(9), P(3)}))
    return out

expected_compared = [True, True, True, True, True, False, False, True, False, True, False, False, True, True,
                     False, True, False, "chain", True, False, ("KeyError", "9"), ("KeyError", "9"),
                     ("KeyError", "9")]

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
    return results(), updated(), compared()

assert_eq(main(), (expected, expected_updated, expected_compared))
assert_eq(results(), expected)
assert_eq(updated(), expected_updated)
assert_eq(compared(), expected_compared)
