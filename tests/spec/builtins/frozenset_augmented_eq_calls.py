# spec: PLS-315 26.3.2, 14.3
# description: A frozenset's augmented assignments |=, &=, -= and ^= with
# a set whose elements' Python __eq__, which may loop, compares them
# are its operators: they bind a new frozenset and leave the old one,
# comparing the entries as the operators do; an exception of __eq__
# propagates, and an operand that is no set raises TypeError. Inside
# functions as at module level.
from harness import *

log = []
class E:
    def __init__(self, v): self.v = v
    def __hash__(self): return 1
    def __eq__(self, o):
        for _ in range(2): pass
        log.append((self.v, o.v))
        if self.v == 99: raise LookupError("eq")
        return self.v == o.v
    def __repr__(self): return "E%d" % self.v
def t(f):
    try: r = f()
    except Exception as e: r = type(e).__name__ + ": " + str(e)
    out = (r, log[:]); del log[:]; return out
def results():
    out = []
    for op in ("|", "&", "-", "^"):
        def f(op=op):
            a = frozenset([E(1), E(2)]); keep = a; b = {E(2), E(3)}
            if op == "|": a |= b
            elif op == "&": a &= b
            elif op == "-": a -= b
            else: a ^= b
            return type(a).__name__, sorted(e.v for e in a), keep is a, sorted(e.v for e in keep)
        out.append(t(f))
    def bad():
        a = frozenset([E(99)]); a &= {E(2)}
    out.append(t(bad))
    def other():
        a = frozenset([E(1)]); a &= [E(1)]
    out.append(t(other))
    return out

expected = [(('frozenset', [1, 2, 3], False, [1, 2]), [(1, 2), (2, 3), (1, 2), (2, 2), (1, 3), (2, 3)]),
            (('frozenset', [2], False, [1, 2]), [(1, 2), (2, 3), (1, 2), (2, 2), (1, 3), (2, 3)]),
            (('frozenset', [1], False, [1, 2]), [(1, 2), (2, 3), (2, 1), (3, 1), (2, 2)]),
            (('frozenset', [1, 3], False, [1, 2]), [(1, 2), (2, 3), (2, 1), (3, 1), (2, 1), (3, 1), (2, 2)]),
            ('LookupError: eq', [(99, 2)]),
            ("TypeError: unsupported operand type(s) for &=: 'frozenset' and 'list'", [])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
