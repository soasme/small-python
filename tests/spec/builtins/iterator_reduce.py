# spec: PLS-315 27.1.1, 29.9.1, 9.3.2
# description: __reduce__ and __setstate__ of the intrinsic iterators, the builtins lookup they make first, and the generic alias iterator.
from harness import *

builtins = vars(iter.__self__)

def drained(it):
    for _ in it:
        pass
    return it

# Sequence iterators: (iter, (s,), i), or (iter, (empty,)) once exhausted.
for s, empty in (([1, 2], []), ((1, 2), ()), ("ab", ""), ("\xe9\xe8", ""), (b"ab", ()), (bytearray(b"ab"), ())):
    it = iter(s)
    assert_eq(it.__reduce__(), (iter, (s,), 0))
    next(it)
    assert_eq(it.__reduce__(), (iter, (s,), 1))
    assert_eq(drained(it).__reduce__(), (iter, (empty,)))

# Range iterators: the rest of the range, then None.
it = iter(range(1, 10, 3))
next(it)
assert_eq(it.__reduce__(), (iter, (range(4, 10, 3),), None))
it = reversed(range(3))
assert_eq(it.__reduce__(), (iter, (range(2, -1, -1),), None))
big = 2 ** 64
it = iter(range(big, big + 3))
next(it)
assert_eq((type(it).__name__, it.__reduce__()), ("longrange_iterator", (iter, (range(big + 1, big + 3),), None)))

# Dict and set iterators: a list of what a copy would still produce.
d = {1: "a", 2: "b", 3: "c"}
for make, items in ((lambda: iter(d), [1, 2, 3]), (lambda: iter(d.values()), ["a", "b", "c"]),
                    (lambda: iter(d.items()), [(1, "a"), (2, "b"), (3, "c")]),
                    (lambda: reversed(d), [3, 2, 1]), (lambda: reversed(d.values()), ["c", "b", "a"]),
                    (lambda: reversed(d.items()), [(3, "c"), (2, "b"), (1, "a")])):
    it = make()
    assert_eq(it.__reduce__(), (iter, (items,)))
    next(it)
    assert_eq(it.__reduce__(), (iter, (items[1:],)))
    # Reducing did not advance the iterator itself.
    assert_eq(list(it), items[1:])
    assert_eq(it.__reduce__(), (iter, ([],)))
it = iter({7})
assert_eq((it.__reduce__(), list(it), it.__reduce__()), ((iter, ([7],)), [7], (iter, ([],))))
it = iter(d)
d[4] = "d"
e = assert_raises(RuntimeError, it.__reduce__)
assert_eq(str(e), "dictionary changed size during iteration")
del d[4]

# Reverse iterators.
l = [1, 2, 3]
it = reversed(l)
assert_eq(type(it).__name__, "list_reverseiterator")
assert_eq(it.__reduce__(), (reversed, (l,), 2))
next(it)
assert_eq(it.__reduce__(), (reversed, (l,), 1))
assert_eq(drained(it).__reduce__(), (reversed, ([],)))
assert_eq(reversed([]).__reduce__(), (reversed, ([],)))
t = (1, 2, 3)
it = reversed(t)
assert_eq((type(it), it.__reduce__()), (reversed, (reversed, (t,), 2)))
assert_eq(drained(it).__reduce__(), (reversed, ((),)))
class Rev(reversed):
    pass
it = Rev(t)
assert_eq(it.__reduce__(), (Rev, (t,), 2))
for state, expected in ((-5, []), (-1, []), (0, [1]), (1, [2, 1]), (2, [3, 2, 1]), (9, [3, 2, 1])):
    for make in (lambda: reversed([1, 2, 3]), lambda: reversed((1, 2, 3))):
        it = make()
        it.__setstate__(state)
        assert_eq(list(it), expected, state)
it = drained(reversed((1, 2)))
it.__setstate__(1)
assert_eq(list(it), [])

# enumerate, filter, map, zip name their class and hold their iterators.
inner = iter("ab")
class Enum(enumerate):
    pass
for cls in (enumerate, Enum):
    e = cls(inner, 5)
    assert_eq(e.__reduce__(), (cls, (inner, 5)))
next(e)
assert_eq(e.__reduce__(), (Enum, (inner, 6)))
inner = iter([0, 1])
assert_eq(filter(None, inner).__reduce__(), (filter, (None, inner)))
a, b = iter("ab"), iter("cd")
assert_eq(map(max, a, b).__reduce__(), (map, (max, a, b)))
assert_eq(map(max, a, b, strict=True).__reduce__(), (map, (max, a, b), True))
assert_eq(zip(a, b).__reduce__(), (zip, (a, b)))
z = zip(a, b, strict=True)
assert_eq(z.__reduce__(), (zip, (a, b), True))
z.__setstate__(0)
assert_eq(z.__reduce__(), (zip, (a, b)))
z = zip("a", "bc")
z.__setstate__("yes")
e = assert_raises(ValueError, list, z)
assert_eq(str(e), "zip() argument 2 is longer than argument 1")
m = map(max, [1], [1, 2])
m.__setstate__([1])
e = assert_raises(ValueError, list, m)
assert_eq(str(e), "map() argument 2 is longer than argument 1")

# Which iterators have __setstate__.
for it, has in ((iter([]), True), (iter(()), True), (iter(""), True), (iter(b""), True), (iter(range(0)), True),
                (reversed([]), True), (reversed(()), True), (zip(), True), (map(abs, ()), True),
                (iter({}), False), (iter(set()), False), (reversed({}), False), (enumerate(()), False),
                (filter(None, ()), False), (iter(int, 0), False), (iter(t"x"), False)):
    assert_eq(hasattr(it, "__setstate__"), has, type(it).__name__)
assert_false(hasattr(iter(t"x"), "__reduce__") and type(iter(t"x")).__reduce__ is not object.__reduce__)

# __setstate__ of the sequence iterators.
it = iter((1, 2, 3))
it.__setstate__(-1)
assert_eq(list(it), [1, 2, 3])
it = iter([1, 2, 3])
it.__setstate__(-1)
assert_eq((it.__reduce__(), list(it)), ((iter, ([],)), []))
it.__setstate__(1)
assert_eq(list(it), [2, 3])
it = iter("abc")
it.__setstate__(5)
assert_eq(list(it), [])
for target in (iter([1]), reversed([1]), reversed((1,))):
    e = assert_raises(TypeError, target.__setstate__, "1")
    assert_eq(str(e), "an integer is required")
    e = assert_raises(OverflowError, target.__setstate__, 2 ** 70)
    assert_eq(str(e), "Python int too large to convert to C ssize_t")
e = assert_raises(TypeError, zip().__setstate__)
assert_eq(str(e), "zip.__setstate__() takes exactly one argument (0 given)")
e = assert_raises(TypeError, map(abs, ()).__setstate__, 1, 2)
assert_eq(str(e), "map.__setstate__() takes exactly one argument (2 given)")
e = assert_raises(TypeError, enumerate(()).__reduce__, 1)
assert_eq(str(e), "enumerate.__reduce__() takes no arguments (1 given)")
e = assert_raises(TypeError, enumerate.__reduce__, [])
assert_eq(str(e), "descriptor '__reduce__' for 'enumerate' objects doesn't apply to a 'list' object")

# __setstate__ of the range iterators.
class Two:
    def __index__(self):
        return 2
it = iter(range(5))
next(it)
it.__setstate__(Two())
assert_eq(list(it), [3, 4])
it = iter(range(5))
it.__setstate__(True)
assert_eq(list(it), [1, 2, 3, 4])
e = assert_raises(TypeError, iter(range(5)).__setstate__, "x")
assert_eq(str(e), "'str' object cannot be interpreted as an integer")
e = assert_raises(OverflowError, iter(range(5)).__setstate__, 2 ** 70)
assert_eq(str(e), "Python int too large to convert to C long")
it = iter(range(big, big + 3))
it.__setstate__(2 ** 70)
assert_eq(list(it), [])
it = iter(range(big, big + 3))
it.__setstate__(-2 ** 70)
assert_eq(list(it), [big, big + 1, big + 2])
e = assert_raises(TypeError, iter(range(big, big + 1)).__setstate__, Two())
assert_eq(str(e), "state must be an int, not Two")

# The builtins lookup comes first, by key equality, and can exhaust the iterator.
class Key:
    def __init__(self, name, it):
        self.name, self.it = name, it
    def __hash__(self):
        return hash(self.name)
    def __eq__(self, other):
        list(self.it)
        return other == self.name
def reduce_with_key(name, it):
    original = builtins.pop(name)
    builtins[Key(name, it)] = original
    try:
        return it.__reduce__()
    finally:
        del builtins[name]
        builtins[name] = original
for it, expected in ((iter("xyz"), (iter, ("",))), (iter([1, 2]), (iter, ([],))), (iter((1,)), (iter, ((),))),
                     (iter({1: 2}), (iter, ([1],))), (iter(iter([1, 2, 0]).__next__, 0), (iter, ((),))), (iter(Seq := type("Seq", (), {"__getitem__": lambda s, i: [0][i]})()), (iter, ((),))),
                     (iter(tuple[int]), (iter, ((),)))):
    assert_eq(reduce_with_key("iter", it), expected, type(it).__name__)
assert_eq(reduce_with_key("reversed", reversed([1, 2])), (reversed, ([],)))
original = builtins.pop("iter")
try:
    e = assert_raises(AttributeError, iter_ := original([1]).__reduce__)
finally:
    builtins["iter"] = original
assert_eq(e.args, ("iter",))

# The generic alias iterator.
it = iter(tuple[int])
assert_eq((type(it).__name__, type(it).__module__), ("generic_alias_iterator", "builtins"))
assert_eq(it.__reduce__(), (iter, (tuple[int],)))
assert_eq(next(it), (*tuple[int],)[0])
assert_eq(it.__reduce__(), (iter, ((),)))
assert_raises(StopIteration, next, it)
e = assert_raises(TypeError, type, "X", (type(it),), {})
assert_eq(str(e), "type 'generic_alias_iterator' is not an acceptable base type")
