# spec: PLS-315 25.2
# description: tuple construction, repr, and the tuple hash algorithm.
from harness import *

assert_eq(tuple(), ())
assert_eq(tuple([1, 2]), (1, 2))
assert_eq(tuple("ab"), ("a", "b"))
assert_raises(TypeError, lambda: tuple(iterable=[1]))
e = assert_raises(TypeError, tuple, [1], [2])
assert_eq(str(e), "tuple expected at most 1 argument, got 2")
assert_eq(repr((1,)), "(1,)")
assert_eq(repr(()), "()")
assert_eq(repr((1, "a", None)), "(1, 'a', None)")
inner = []
t = (inner,)
inner.append(t)
assert_eq(repr(t), "([(...)],)")
assert_raises(TypeError, hash, ([],))

M = 1 << 64
P1, P2, P5 = 11400714785074694791, 14029467366897019727, 2870177450012600261
def tuple_hash(items):
    acc = P5
    for x in items:
        lane = hash(x) % M
        acc = (acc + lane * P2) % M
        acc = ((acc << 31) | (acc >> 33)) % M
        acc = (acc * P1) % M
    acc = (acc + (len(items) ^ (P5 ^ 3527539))) % M
    signed = acc - M if acc >= 1 << 63 else acc
    return 1546275796 if signed == -1 else signed
if True:
    width_ok = hash(1 << 40) == 1 << 40   # a 64-bit hash width (Annex D)
    if width_ok:
        for value in ((), (1,), (1, 2, 3), ("a", -1, 2.5, None), ((1, 2), (3,))):
            assert_eq(hash(value), tuple_hash(value), repr(value))
assert_eq(hash((1, 2)), hash((1, 2)))
class Hashy:
    def __hash__(self):
        return 7
assert_eq(hash((Hashy(),)), hash((7,)))
