# spec: PLS-315 7.7.1
# description: __iter__ and the __getitem__ sequence protocol in for loops.
from harness import *


def test_container(x):
    assert 3 in x
    assert 4 not in x
    assert list(x) == list(iter(x))
    assert list(x) == [0, 1, 2, 3]
    assert [*x] == [0, 1, 2, 3]
    lst = []
    lst.extend(x)
    assert lst == [0, 1, 2, 3]


class C:
    def __iter__(self):
        return iter([0, 1, 2, 3])


test_container(C())


class C:
    def __getitem__(self, x):
        return (0, 1, 2, 3)[x]  # raises IndexError on x==4


test_container(C())


class C:
    def __getitem__(self, x):
        if x > 3:
            raise StopIteration
        return x


test_container(C())


class C:
    pass


assert_raises(TypeError, lambda: 5 in C())
assert_raises(TypeError, iter, C)

it = iter([1, 2, 3, 4, 5])
call_it = iter(lambda: next(it), 4)
assert list(call_it) == [1, 2, 3]

# A length hint that is unusable leaves the result empty, not failed.
class Hinted:
    def __iter__(self): return self
    def __next__(self): raise StopIteration
    def __length_hint__(self): return NotImplemented
class Failing(Hinted):
    def __length_hint__(self): raise TypeError("x")
assert_eq(list(Hinted()), [])
assert_eq(list(Failing()), [])

# A __len__ that raises TypeError is no length: the hint is consulted next.
class Unsized:
    def __iter__(self): return iter([1, 2])
    def __len__(self): raise TypeError("no len")
    def __length_hint__(self): return 5
assert_eq(list(Unsized()), [1, 2])
class BadLength(Unsized):
    def __len__(self): raise ValueError("bad")
assert_raises(ValueError, list, BadLength(), message="bad")
