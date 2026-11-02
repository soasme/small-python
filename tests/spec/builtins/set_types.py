# spec: PLS-315 26.3
# description: set and frozenset: construction, operators, methods, iteration, repr, and the frozenset hash.
from harness import *

assert_eq(set("abca"), {"a", "b", "c"})
assert_eq(frozenset([1, 1, 2]), frozenset({1, 2}))
# SetAdd keeps the element already present.
s = set([1, 1.0, True])
assert_eq(len(s), 1)
assert_type(next(iter(s)), int)
e = assert_raises(TypeError, set, [], [])
assert_eq(str(e), "set expected at most 1 argument, got 2")
e = assert_raises(TypeError, set, iterable=[])
assert_eq(str(e), "set() takes no keyword arguments")
assert_raises(TypeError, set, [[]])

a, b = {1, 2, 3}, frozenset({3, 4})
assert_eq(a | b, {1, 2, 3, 4})
assert_type(a | b, set)
assert_type(b | a, frozenset)
assert_eq(a & b, {3})
assert_eq(a - b, {1, 2})
assert_eq(a ^ b, {1, 2, 4})
assert_true({1} <= a and {1} < a and not a < a and a <= a)
assert_true(a >= {1} and a > {1})
assert_eq(set(), frozenset())
assert_eq({1, 2}, frozenset({2, 1}))
assert_true(a.isdisjoint([7, 8]))
assert_eq(a.union([4], (5,)), {1, 2, 3, 4, 5})
assert_eq(a.intersection([1, 2], {2}), {2})
assert_eq(a.difference([1], [2]), {3})
assert_eq(a.symmetric_difference([3, 9]), {1, 2, 9})
assert_true(a.issubset(range(5)))
assert_true(a.issuperset([1]))
e = assert_raises(TypeError, lambda: a | [4])
assert_eq(str(e), "unsupported operand type(s) for |: 'set' and 'list'")

s = {1, 2}
same = s
s |= {3}
s &= {1, 3, 5}
s -= {5}
s ^= {7}
assert_is(s, same)
assert_eq(s, {1, 3, 7})
s.update([8], [9])
s.intersection_update(range(8))
s.difference_update([1])
s.symmetric_difference_update([3, 4])
assert_eq(s, {4, 7})
s.add(5)
s.discard(99)
s.remove(5)
e = assert_raises(KeyError, s.remove, 99)
assert_eq(e.args, (99,))
assert_true(s.pop() in {4, 7})
s.clear()
e = assert_raises(KeyError, s.pop)
assert_eq(str(e), "'pop from an empty set'")
c = a.copy()
assert_true(c == a and c is not a)
assert_raises(TypeError, hash, set())
assert_raises(TypeError, lambda: {[]})
def inplace(): t = {1}; t |= [2]
assert_raises(TypeError, inplace)

# A set argument is looked up as a frozenset.
nested = {frozenset({1, 2})}
assert_true({1, 2} in nested)
nested.remove({2, 1})
assert_eq(nested, set())
nested.add(frozenset({3}))
nested.discard({3})
assert_eq(nested, set())

assert_eq(repr(set()), "set()")
assert_eq(repr({1}), "{1}")
assert_eq(repr(frozenset()), "frozenset()")
assert_eq(repr(frozenset({1})), "frozenset({1})")
class MySet(set): pass
class MyFrozen(frozenset): pass
assert_eq(repr(MySet()), "MySet()")
assert_eq(repr(MySet([1])), "MySet({1})")
assert_eq(repr(MyFrozen([1])), "MyFrozen({1})")

# Iteration order is stable for an unmodified set; size changes are detected.
s = set(range(20))
assert_eq(list(s), list(s))
it = iter(s)
next(it)
s.add(100)
e = assert_raises(RuntimeError, next, it)
assert_eq(str(e), "Set changed size during iteration")

M = 1 << 64
def shuffle(h):
    h %= M
    return (((h ^ 89869747) ^ (h << 16)) * 3644798167) % M
def frozenset_hash(items):
    acc = 0
    for x in items:
        acc ^= shuffle(hash(x))
    acc ^= ((len(items) + 1) * 1927868237) % M
    acc ^= (acc >> 11) ^ (acc >> 25)
    acc = (acc * 69069 + 907133923) % M
    signed = acc - M if acc >= 1 << 63 else acc
    return 590923713 if signed == -1 else signed
if hash(1 << 40) == 1 << 40:   # a 64-bit hash width (Annex D)
    for value in (frozenset(), frozenset({1}), frozenset({1, 2, 3}), frozenset({"a", None, 2.5})):
        assert_eq(hash(value), frozenset_hash(value), repr(value))
assert_eq(hash(frozenset([1, 2])), hash(frozenset([2, 1])))

# A set subclass argument is looked up as a frozenset too; remove's KeyError
# has the argument itself.
for key in ({5}, MySet([5])):
    nested = {frozenset({5})}
    assert_true(key in nested)
    nested.discard(key)
    assert_eq(nested, set())
    error = assert_raises(KeyError, nested.remove, key)
    assert_is(error.args[0], key)

# A recursive repr shows the type name; the reduction lists the elements.
class Wrapper:
    def __repr__(self):
        return repr(self.value)
for kind, shown in ((set, "{set(...)}"), (frozenset, "frozenset({frozenset(...)})"),
                    (MySet, "MySet({MySet(...)})"), (MyFrozen, "MyFrozen({MyFrozen(...)})")):
    w = Wrapper()
    w.value = kind([w])
    assert_eq(repr(w.value), shown)
assert_eq({1}.__reduce__(), (set, ([1],), None))
assert_eq(frozenset().__reduce_ex__(0), (frozenset, ([],), None))
tagged = MyFrozen([2])
tagged.tag = 3
assert_eq(tagged.__reduce__(), (MyFrozen, ([2],), {"tag": 3}))
assert_eq(pickle.loads(pickle.dumps(tagged)).tag, 3)

# Copying stored keys reuses their hashes (26).
class Counted:
    calls = 0
    def __hash__(self):
        Counted.calls += 1
        return 7
keys = dict.fromkeys(Counted() for i in range(3))
elements = set(keys)
for copy in (lambda: set(keys), lambda: frozenset(elements), lambda: MySet(elements), lambda: set().update(keys),
             lambda: elements.union(keys), lambda: elements.difference(keys), lambda: elements ^ frozenset(elements),
             lambda: dict.fromkeys(elements), lambda: dict(keys)):
    Counted.calls = 0
    copy()
    assert_eq(Counted.calls, 0)

# issuperset and isdisjoint stop reading an iterable once decided, and
# issubset and intersection once every element is found.
items = iter([1, 2, 3])
assert_false({1}.isdisjoint(items))
assert_eq(list(items), [2, 3])
items = iter([1, 2, 3])
assert_false({2}.issuperset(items))
assert_eq(list(items), [2, 3])
items = iter([5, 2, 3])
assert_true({2}.issubset(items))
assert_eq(list(items), [3])
items = iter([5, 2, 3])
assert_eq({2}.intersection(items), {2})
assert_eq(list(items), [3])

# Comparisons may empty the operand being merged; the merge stays safe.
class Clears:
    def __hash__(self):
        return 0
    def __eq__(self, other):
        operand.clear()
        return False
for merge in ("update", "symmetric_difference_update", "union", "symmetric_difference"):
    operand = set()
    operand = {Clears() for i in range(10)}
    getattr({0}, merge)(operand)

# A subset test against a set keeps no reference to it.
reclaimed = []
class Finalized:
    def __del__(self):
        reclaimed.append(True)
operand = {Finalized()}
assert_true(set().issubset(operand))
del operand
host.collect()
assert_eq(reclaimed, [True])
