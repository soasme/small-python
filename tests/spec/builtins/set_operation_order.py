# spec: PLS-315 26.3.2
# description: a set operation of two sets compares the entries CPython's
# algorithms compare: a union looks the right set's entries up in the
# left's copy; an intersection the smaller set's, the right's when as large,
# in the other, then each found in the result; a difference the left's
# entries in the right, then each missing one in the result, or, for a
# left set more than four times larger, the right's in the left's copy to
# discard; a symmetric difference the left's entries in the right's copy,
# discarding each found and looking one missing up again to add it; the
# updates the right set's entries in the set; the comparisons the subset
# side's entries in the other, and isdisjoint the smaller's, the right's
# when as large, until one decides; in a function on the machine and in
# one that is not, alike.
from harness import *

log = []

class E:
    def __init__(self, side, v): self.side, self.v = side, v
    def __hash__(self): return 1
    def __eq__(self, other):
        log.append(self.side + str(self.v))
        return self.v == other.v

def build(side, n, start):
    for _ in (): pass
    return {E(side, v) for v in range(start, start + n)}

def m0(a, b):
    for _ in (): pass
    return a | b
def c0(a, b):
    return a | b

def m1(a, b):
    for _ in (): pass
    return a & b
def c1(a, b):
    return a & b

def m2(a, b):
    for _ in (): pass
    return a & b
def c2(a, b):
    return a & b

def m3(a, b):
    for _ in (): pass
    return a - b
def c3(a, b):
    return a - b

def m4(a, b):
    for _ in (): pass
    return a - b
def c4(a, b):
    return a - b

def m5(a, b):
    for _ in (): pass
    return a ^ b
def c5(a, b):
    return a ^ b

def m6(a, b):
    for _ in (): pass
    return a <= b
def c6(a, b):
    return a <= b

def m7(a, b):
    for _ in (): pass
    return a < b
def c7(a, b):
    return a < b

def m8(a, b):
    for _ in (): pass
    return a >= b
def c8(a, b):
    return a >= b

def m9(a, b):
    for _ in (): pass
    return a > b
def c9(a, b):
    return a > b

def m10(a, b):
    for _ in (): pass
    return a == b
def c10(a, b):
    return a == b

def m11(a, b):
    for _ in (): pass
    return a.union(b)
def c11(a, b):
    return a.union(b)

def m12(a, b):
    for _ in (): pass
    return a.intersection(b)
def c12(a, b):
    return a.intersection(b)

def m13(a, b):
    for _ in (): pass
    return a.difference(b)
def c13(a, b):
    return a.difference(b)

def m14(a, b):
    for _ in (): pass
    return a.symmetric_difference(b)
def c14(a, b):
    return a.symmetric_difference(b)

def m15(a, b):
    for _ in (): pass
    return a.issubset(b)
def c15(a, b):
    return a.issubset(b)

def m16(a, b):
    for _ in (): pass
    return a.issuperset(b)
def c16(a, b):
    return a.issuperset(b)

def m17(a, b):
    for _ in (): pass
    return a.isdisjoint(b)
def c17(a, b):
    return a.isdisjoint(b)

def m18(a, b):
    for _ in (): pass
    return a.isdisjoint(b)
def c18(a, b):
    return a.isdisjoint(b)

def m19(a, b):
    for _ in (): pass
    a.update(b)
    return a
def c19(a, b):
    a.update(b)
    return a

def m20(a, b):
    for _ in (): pass
    a.intersection_update(b)
    return a
def c20(a, b):
    a.intersection_update(b)
    return a

def m21(a, b):
    for _ in (): pass
    a.difference_update(b)
    return a
def c21(a, b):
    a.difference_update(b)
    return a

def m22(a, b):
    for _ in (): pass
    a.symmetric_difference_update(b)
    return a
def c22(a, b):
    a.symmetric_difference_update(b)
    return a

CASES = [
    (m0, c0, 'a | b', 3, 3, [1, 2, 3, 4], ['a1', 'a2', 'a1', 'a2', 'a3', 'a1', 'a2', 'a3']),
    (m1, c1, 'a & b', 3, 3, [2, 3], ['a1', 'a2', 'a1', 'a2', 'a3', 'b2', 'a1', 'a2', 'a3']),
    (m2, c2, 'a & b', 3, 1, [2], ['a1', 'a2']),
    (m3, c3, 'a - b', 3, 3, [1], ['b2', 'b3', 'b4', 'b2', 'b2', 'b3']),
    (m4, c4, 'a - b', 8, 1, [1, 3, 4, 5, 6, 7, 8], ['a1', 'a4', 'a5', 'a2']),
    (m5, c5, 'a ^ b', 3, 3, [1, 4], ['b2', 'b3', 'b4', 'b2', 'b3', 'b4', 'b2', 'b3']),
    (m6, c6, 'a <= b', 2, 3, False, ['b2', 'b3', 'b4']),
    (m7, c7, 'a < b', 2, 3, False, ['b2', 'b3', 'b4']),
    (m8, c8, 'a >= b', 3, 2, True, ['a1', 'a2', 'a1', 'a2', 'a3']),
    (m9, c9, 'a > b', 3, 2, True, ['a1', 'a2', 'a1', 'a2', 'a3']),
    (m10, c10, 'a == b', 3, 3, False, ['b2', 'b3', 'b4']),
    (m11, c11, 'a.union(b)', 3, 3, [1, 2, 3, 4], ['a1', 'a2', 'a1', 'a2', 'a3', 'a1', 'a2', 'a3']),
    (m12, c12, 'a.intersection(b)', 2, 3, [2], ['b2', 'b3', 'b4', 'b2']),
    (m13, c13, 'a.difference(b)', 3, 3, [1], ['b2', 'b3', 'b4', 'b2', 'b2', 'b3']),
    (m14, c14, 'a.symmetric_difference(b)', 3, 3, [1, 4], ['b2', 'b3', 'b4', 'b2', 'b3', 'b4', 'b2', 'b3']),
    (m15, c15, 'a.issubset(b)', 2, 3, False, ['b2', 'b3', 'b4']),
    (m16, c16, 'a.issuperset(b)', 3, 2, True, ['a1', 'a2', 'a1', 'a2', 'a3']),
    (m17, c17, 'a.isdisjoint(b)', 3, 3, False, ['a1', 'a2']),
    (m18, c18, 'a.isdisjoint(b)', 2, 3, False, ['b2', 'b3', 'b4', 'b2']),
    (m19, c19, 'a.update(b)', 3, 3, [1, 2, 3, 4], ['a1', 'a2', 'a1', 'a2', 'a3', 'a1', 'a2', 'a3']),
    (m20, c20, 'a.intersection_update(b)', 3, 3, [2, 3], ['a1', 'a2', 'a1', 'a2', 'a3', 'b2', 'a1', 'a2', 'a3']),
    (m21, c21, 'a.difference_update(b)', 3, 3, [1], ['a1', 'a2', 'a1', 'a3', 'a1']),
    (m22, c22, 'a.symmetric_difference_update(b)', 3, 3, [1, 4], ['a1', 'a2', 'a1', 'a3', 'a1', 'a1'])
]

def run(f, n, m):
    for _ in (): pass
    a = build("a", n, 1); b = build("b", m, 2)
    log.clear()
    r = f(a, b)
    return (r if isinstance(r, bool) else sorted(e.v for e in r)), log[:]

for machine, plain, expr, n, m, result, compared in CASES:
    for f in (machine, plain):
        got = run(f, n, m)
        if (expr, n) == ("a - b", 8):
            # The left set's entries are compared, in an implementation's
            # order, until the right's is found among them.
            assert_eq((got[0], set(e[0] for e in got[1]), got[1][-1]), (result, {"a"}, "a2"))
        else:
            assert_eq((expr, got), (expr, (result, compared)))

# A frozenset's augmented assignments are its operators.
def frozen():
    for _ in (): pass
    out = []
    for op in ("|", "&", "-", "^"):
        a = frozenset(build("a", 3, 1)); b = build("b", 3, 2)
        log.clear()
        if op == "|": a |= b
        elif op == "&": a &= b
        elif op == "-": a -= b
        else: a ^= b
        out.append((type(a).__name__, sorted(e.v for e in a), log[:]))
    return out

assert_eq(frozen(), [
    ("frozenset", [1, 2, 3, 4], ["a1", "a2", "a1", "a2", "a3", "a1", "a2", "a3"]),
    ("frozenset", [2, 3], ["a1", "a2", "a1", "a2", "a3", "b2", "a1", "a2", "a3"]),
    ("frozenset", [1], ["b2", "b3", "b4", "b2", "b2", "b3"]),
    ("frozenset", [1, 4], ["b2", "b3", "b4", "b2", "b3", "b4", "b2", "b3"]),
])
