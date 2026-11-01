# spec: PLS-315 13.10, 7.8.3
# description: in and not in with __contains__, __iter__, and __getitem__.
from harness import *

# test lists
assert 3 in [1, 2, 3]
assert 3 not in [1, 2]

assert not (3 in [1, 2])
assert not (3 not in [1, 2, 3])

# test strings
assert "foo" in "foobar"
assert "whatever" not in "foobar"

# test bytes
assert b"foo" in b"foobar"
assert b"whatever" not in b"foobar"
assert b"1" < b"2"
assert b"1" <= b"2"
assert b"5" <= b"5"
assert b"4" > b"2"
assert not b"1" >= b"2"
assert b"10" >= b"10"
assert_raises(TypeError, lambda: bytes() > 2)

# test tuple
assert 1 in (1, 2)
assert 3 not in (1, 2)

# test set
assert 1 in set([1, 2])
assert 3 not in set([1, 2])

# test dicts
assert "a" in {"a": 0, "b": 0}
assert "c" not in {"a": 0, "b": 0}
assert 1 in {1: 5, 7: 12}
assert 5 not in {9: 10, 50: 100}
assert True in {True: 5}
assert False not in {True: 5}

# test iter
assert 3 in iter([1, 2, 3])
assert 3 not in iter([1, 2])

# test sequence
assert 1 in range(0, 2)
assert 3 not in range(0, 2)


# test __contains__ in user objects
class MyNotContainingClass:
    pass


assert_raises(TypeError, lambda: 1 in MyNotContainingClass())


class MyContainingClass:
    def __init__(self, value):
        self.value = value

    def __contains__(self, something):
        return something == self.value


assert 2 in MyContainingClass(2)
assert 1 not in MyContainingClass(2)


# A list or tuple compares each item by identity, then equality, holding the
# item and reading the length again while an __eq__ changes the list.
nan = float("nan")
assert nan in [nan] and nan in (nan,)
assert nan not in [float("nan")]
assert 1 not in [] and 1 not in ()
items = []
class Clears:
    def __eq__(self, other):
        items.clear()
        return False
items.extend([Clears(), Clears(), 1])
assert 1 not in items
assert_eq(items, [])
grown = []
class Grows:
    def __eq__(self, other):
        if len(grown) < 4:
            grown.append(Grows())
        return False
grown.append(Grows())
assert 5 not in grown
assert_eq(len(grown), 4)
class Raises:
    def __eq__(self, other):
        raise ValueError("eq")
assert_raises(ValueError, lambda: 1 in [Raises()])
assert_raises(ValueError, lambda: 1 not in (Raises(),))
class Refuses(list):
    def __contains__(self, item):
        return False
assert 1 not in Refuses([1])
