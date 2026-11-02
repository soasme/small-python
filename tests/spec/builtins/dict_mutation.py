# spec: PLS-315 26, 26.1.1, 26.1.2, 26.1.4, 9.6
# description: dicts changed by their own iteration, comparison, and update callbacks; conversion notes; stored hashes and deep frozendict hashing.
from harness import *

# Removing a key and adding one back at the same size is a key change for
# every view, though the key is the same object at the same position.
for view in (lambda d: d, dict.keys, dict.values, dict.items):
    d = {0: 0}
    def churn():
        for item in view(d):
            del d[0]
            d[0] = 0
    error = assert_raises(RuntimeError, churn)
    assert_eq(str(error), "dictionary keys changed during iteration")

# Clearing an empty dict removes nothing.
d = {}
it = iter(d)
d.clear()
assert_eq(list(it), [])

# A reversed iterator that has keys left to produce raises too.
d = dict.fromkeys(range(10))
for i in range(7):
    del d[i]
iterators = [reversed(d), reversed(d.keys()), reversed(d.values()), reversed(d.items())]
for it in iterators:
    next(it)
d.clear()
d.update(dict.fromkeys(range(10)))
for i in range(3, 10):
    del d[i]
for it in iterators:
    error = assert_raises(RuntimeError, list, it)
    assert_eq(str(error), "dictionary keys changed during iteration")

# Replacing values and looking keys up leave iteration alone.
d = dict.fromkeys(range(20), 0)
for k in d:
    d[k] = d[k] + 1
    d.get(-1)
assert_eq(set(d.values()), {1})

# A comparison that empties the left operand only ends the walk.
class Clears:
    def __eq__(self, other):
        left.clear()
        return True
    def __hash__(self):
        return 13
left = {Clears(): 0}
right = {Clears(): 0}
assert_true(left == right)

# A TypeError converting an update element gets a note naming it.
def failing():
    yield "key"
    raise TypeError("oops")
for source, message in (([(1, 2), object()], "object is not iterable"), ([failing()], "oops")):
    error = assert_raises(TypeError, dict, source)
    assert_eq(str(error), message)
    index = len(source) - 1
    assert_eq(error.__notes__, [f"Cannot convert dictionary update sequence element #{index} to a sequence"])
error = assert_raises(TypeError, dict, [([], 1)])
assert_false(hasattr(error, "__notes__"))

# Copying stored keys reuses their hashes, into a dict subclass too.
class Counted:
    calls = 0
    def __hash__(self):
        Counted.calls += 1
        return 7
class Sub(dict):
    pass
keys = dict.fromkeys(Counted() for i in range(3))
for copy in (lambda: Sub(keys), lambda: dict(keys), lambda: {**keys}, lambda: Sub().update(keys)):
    Counted.calls = 0
    copy()
    assert_eq(Counted.calls, 0)

# Hashing nested frozendicts deeper than the implementation can recurse.
nested = frozendict({0: 0})
for i in range(500_000):
    nested = frozendict({0: nested})
error = assert_raises(RecursionError, hash, nested)
assert_true(str(error).endswith(" while hashing a frozendict"), str(error))
