# spec: PLS-315 26.3.2, 7.2.4
# description: an operand that is an instance of a subclass of set or
# frozenset whose class defines no Python method for the operation is
# operated on as its set, comparing elements in the same order, a new
# result of set or frozenset, not the subclass, an in-place operator's the
# instance itself; a comparison with an instance of a proper subclass of
# the other operand's type takes the subclass's reflected comparison
# first (RichCompare step 3), so its elements are looked up in the other.
# A class's own Python method is called instead. Lists and tuples compare
# a subclass's instance likewise, its items first. For elements whose
# __eq__ runs on the machine and those whose __eq__ does not.
from harness import *

log = []

class M:
    """An element whose __eq__ has a loop."""
    def __init__(self, v): self.v = v
    def __hash__(self): return 1
    def __eq__(self, o):
        for _ in (): pass
        log.append(self.v)
        return isinstance(o, (M, W)) and self.v == o.v

class W(M):
    """An element whose __eq__ has none."""
    __hash__ = M.__hash__
    def __eq__(self, o):
        log.append(self.v)
        return isinstance(o, (M, W)) and self.v == o.v

class S(set): pass
class F(frozenset): pass
class Own(set):
    def __or__(self, o): return "own"
    def __eq__(self, o): return "own eq"

def shown(r):
    return (type(r).__name__, sorted(x.v for x in r)) if isinstance(r, (set, frozenset)) else r

def binary(op, a, b):
    for _ in (): pass
    if op == "|": return a | b
    if op == "&": return a & b
    if op == "-": return a - b
    if op == "^": return a ^ b
    if op == "==": return a == b
    if op == "!=": return a != b
    if op == "<=": return a <= b
    return a > b

def inplace(op, a, b):
    for _ in (): pass
    if op == "|=": a |= b
    elif op == "&=": a &= b
    elif op == "-=": a -= b
    else: a ^= b
    return a

def cases(e):
    for _ in (): pass
    out = []
    for ka, kb in ((S, set), (set, S), (F, S)):
        for op in ("|", "&", "-", "^", "==", "!=", "<=", ">"):
            a, b = ka(e(x) for x in (1, 2, 3)), kb(e(x) for x in (2, 3, 4))
            log.clear()
            out.append((ka.__name__, kb.__name__, op, shown(binary(op, a, b)), log[:]))
        for op in ("|=", "&=", "-=", "^="):
            a, b = ka(e(x) for x in (1, 2, 3)), kb(e(x) for x in (2, 3, 4))
            log.clear()
            r = inplace(op, a, b)
            out.append((ka.__name__, kb.__name__, op, r is a, shown(r), log[:]))
        for name in ("union", "intersection", "difference", "issubset", "isdisjoint", "symmetric_difference_update"):
            a, b = ka(e(x) for x in (1, 2, 3)), kb(e(x) for x in (2, 3, 4))
            if not hasattr(a, name): continue
            log.clear()
            out.append((ka.__name__, kb.__name__, name, shown(getattr(a, name)(b)), shown(a), log[:]))
    o = Own({e(1)})
    out.append((binary("|", o, {e(2)}), binary("==", {e(1)}, o), binary("!=", o, {e(1)})))
    return out

expected = [('S', 'set', '|', ('set', [1, 2, 3, 4]), [1, 2, 1, 2, 3, 1, 2, 3]),
 ('S', 'set', '&', ('set', [2, 3]), [1, 2, 1, 2, 3, 2, 1, 2, 3]),
 ('S', 'set', '-', ('set', [1]), [2, 3, 4, 2, 2, 3]),
 ('S', 'set', '^', ('set', [1, 4]), [2, 3, 4, 2, 3, 4, 2, 3]),
 ('S', 'set', '==', False, [2, 3, 4]),
 ('S', 'set', '!=', True, [2, 3, 4]),
 ('S', 'set', '<=', False, [2, 3, 4]),
 ('S', 'set', '>', False, []),
 ('S', 'set', '|=', True, ('S', [1, 2, 3, 4]), [1, 2, 1, 2, 3, 1, 2, 3]),
 ('S', 'set', '&=', True, ('S', [2, 3]), [1, 2, 1, 2, 3, 2, 1, 2, 3]),
 ('S', 'set', '-=', True, ('S', [1]), [1, 2, 1, 3, 1]),
 ('S', 'set', '^=', True, ('S', [1, 4]), [1, 2, 1, 3, 1, 1]),
 ('S', 'set', 'union', ('set', [1, 2, 3, 4]), ('S', [1, 2, 3]), [1, 2, 1, 2, 3, 1, 2, 3]),
 ('S', 'set', 'intersection', ('set', [2, 3]), ('S', [1, 2, 3]), [1, 2, 1, 2, 3, 2, 1, 2, 3]),
 ('S', 'set', 'difference', ('set', [1]), ('S', [1, 2, 3]), [2, 3, 4, 2, 2, 3]),
 ('S', 'set', 'issubset', False, ('S', [1, 2, 3]), [2, 3, 4]),
 ('S', 'set', 'isdisjoint', False, ('S', [1, 2, 3]), [1, 2]),
 ('S', 'set', 'symmetric_difference_update', None, ('S', [1, 4]), [1, 2, 1, 3, 1, 1]),
 ('set', 'S', '|', ('set', [1, 2, 3, 4]), [1, 2, 1, 2, 3, 1, 2, 3]),
 ('set', 'S', '&', ('set', [2, 3]), [1, 2, 1, 2, 3, 2, 1, 2, 3]),
 ('set', 'S', '-', ('set', [1]), [2, 3, 4, 2, 2, 3]),
 ('set', 'S', '^', ('set', [1, 4]), [2, 3, 4, 2, 3, 4, 2, 3]),
 ('set', 'S', '==', False, [1, 2, 1, 2, 3, 1, 2, 3]),
 ('set', 'S', '!=', True, [1, 2, 1, 2, 3, 1, 2, 3]),
 ('set', 'S', '<=', False, [2, 3, 4]),
 ('set', 'S', '>', False, []),
 ('set', 'S', '|=', True, ('set', [1, 2, 3, 4]), [1, 2, 1, 2, 3, 1, 2, 3]),
 ('set', 'S', '&=', True, ('set', [2, 3]), [1, 2, 1, 2, 3, 2, 1, 2, 3]),
 ('set', 'S', '-=', True, ('set', [1]), [1, 2, 1, 3, 1]),
 ('set', 'S', '^=', True, ('set', [1, 4]), [1, 2, 1, 3, 1, 1]),
 ('set', 'S', 'union', ('set', [1, 2, 3, 4]), ('set', [1, 2, 3]), [1, 2, 1, 2, 3, 1, 2, 3]),
 ('set', 'S', 'intersection', ('set', [2, 3]), ('set', [1, 2, 3]), [1, 2, 1, 2, 3, 2, 1, 2, 3]),
 ('set', 'S', 'difference', ('set', [1]), ('set', [1, 2, 3]), [2, 3, 4, 2, 2, 3]),
 ('set', 'S', 'issubset', False, ('set', [1, 2, 3]), [2, 3, 4]),
 ('set', 'S', 'isdisjoint', False, ('set', [1, 2, 3]), [1, 2]),
 ('set', 'S', 'symmetric_difference_update', None, ('set', [1, 4]), [1, 2, 1, 3, 1, 1]),
 ('F', 'S', '|', ('frozenset', [1, 2, 3, 4]), [1, 2, 1, 2, 3, 1, 2, 3]),
 ('F', 'S', '&', ('frozenset', [2, 3]), [1, 2, 1, 2, 3, 2, 1, 2, 3]),
 ('F', 'S', '-', ('frozenset', [1]), [2, 3, 4, 2, 2, 3]),
 ('F', 'S', '^', ('frozenset', [1, 4]), [2, 3, 4, 2, 3, 4, 2, 3]),
 ('F', 'S', '==', False, [2, 3, 4]),
 ('F', 'S', '!=', True, [2, 3, 4]),
 ('F', 'S', '<=', False, [2, 3, 4]),
 ('F', 'S', '>', False, []),
 ('F', 'S', '|=', False, ('frozenset', [1, 2, 3, 4]), [1, 2, 1, 2, 3, 1, 2, 3]),
 ('F', 'S', '&=', False, ('frozenset', [2, 3]), [1, 2, 1, 2, 3, 2, 1, 2, 3]),
 ('F', 'S', '-=', False, ('frozenset', [1]), [2, 3, 4, 2, 2, 3]),
 ('F', 'S', '^=', False, ('frozenset', [1, 4]), [2, 3, 4, 2, 3, 4, 2, 3]),
 ('F', 'S', 'union', ('frozenset', [1, 2, 3, 4]), ('F', [1, 2, 3]), [1, 2, 1, 2, 3, 1, 2, 3]),
 ('F', 'S', 'intersection', ('frozenset', [2, 3]), ('F', [1, 2, 3]), [1, 2, 1, 2, 3, 2, 1, 2, 3]),
 ('F', 'S', 'difference', ('frozenset', [1]), ('F', [1, 2, 3]), [2, 3, 4, 2, 2, 3]),
 ('F', 'S', 'issubset', False, ('F', [1, 2, 3]), [2, 3, 4]),
 ('F', 'S', 'isdisjoint', False, ('F', [1, 2, 3]), [1, 2]),
 ('own', 'own eq', False)]
assert_eq(cases(M), expected)
assert_eq(cases(W), expected)

# A list's or tuple's comparison with its subclass's instance compares the
# instance's items first, unless the subclass has the reflected method.
class Item:
    def __init__(self, v): self.v = v
    def __eq__(self, o):
        log.append(self.v)
        return NotImplemented
    def __gt__(self, o):
        log.append(("gt", self.v))
        return True
class L(list): pass
class T(tuple): pass
class Gt(list):
    def __gt__(self, o):
        log.append("Gt")
        return NotImplemented
def ordered():
    out = []
    for a, b in (([Item(1)], L([Item(2)])), ((Item(1),), T((Item(2),))), ([Item(1)], Gt([Item(2)]))):
        for op in ("==", "<"):
            log.clear()
            out.append((type(b).__name__, op, binary(op, a, b) if op == "==" else a < b, log[:]))
    return out
assert_eq(ordered(), [("L", "==", False, [2, 1]), ("L", "<", True, [2, 1, ("gt", 2)]),
                      ("T", "==", False, [2, 1]), ("T", "<", True, [2, 1, ("gt", 2)]),
                      ("Gt", "==", False, [2, 1]), ("Gt", "<", True, ["Gt", 1, 2, ("gt", 2)])])

# A set or subclass instance as the item of in and not in is no set operation.
def member():
    for _ in (): pass
    x = S({M(1)})
    return [x in [x], frozenset() in {frozenset()}, x not in (), {1} in [S({1})]]
assert_eq(member(), [True, True, True, True])
