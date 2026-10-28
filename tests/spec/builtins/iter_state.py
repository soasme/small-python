# spec: PLS-315 27.1.2, 27.1.3, 19.3.23
# description: The sequence and callable iterators' __reduce__ and __setstate__, and a callable iterator its own callable exhausts.
from harness import *

class Seq:
    def __init__(self, n): self.n = n
    def __getitem__(self, i):
        if i < self.n: return i
        raise IndexError(i)

# The sequence iterator's state is its sequence and index.
s = Seq(3)
it = iter(s)
assert_eq(type(it).__name__, "iterator")
r = it.__reduce__()
assert_true(r[0] is iter and r[1][0] is s)
assert_eq((len(r), len(r[1]), r[2]), (3, 1, 0))
next(it)
assert_eq(it.__reduce__()[2], 1)
it.__setstate__(-42)
assert_eq(next(it), 0)
it.__setstate__(2)
assert_eq(next(it), 2)
# A state past the end is kept; the length is not consulted.
it.__setstate__(10)
assert_eq(it.__reduce__()[2], 10)
s.n = 12
assert_eq(list(it), [10, 11])
assert_eq(it.__reduce__(), (iter, ((),)))
# An exhausted iterator ignores __setstate__.
it.__setstate__(0)
assert_eq(list(it), [])
e = assert_raises(TypeError, it.__setstate__, "1")
assert_eq(str(e), "an integer is required")
e = assert_raises(TypeError, it.__setstate__)
assert_eq(str(e), "iterator.__setstate__() takes exactly one argument (0 given)")
e = assert_raises(TypeError, it.__reduce__, 1)
assert_eq(str(e), "iterator.__reduce__() takes no arguments (1 given)")
e = assert_raises(TypeError, type(it).__reduce__, [])
assert_eq(str(e), "descriptor '__reduce__' for 'iterator' objects doesn't apply to a 'list' object")
# Rebuilding from __reduce__ continues where the iterator was.
it = iter(Seq(5))
next(it); next(it)
func, args, state = it.__reduce__()
copy = func(*args)
copy.__setstate__(state)
assert_eq((list(copy), list(it)), ([2, 3, 4], [2, 3, 4]))

# The callable iterator's state is its callable and sentinel.
f = lambda: 1
c = iter(f, 2)
assert_eq(type(c).__name__, "callable_iterator")
r = c.__reduce__()
assert_true(r[0] is iter and r[1][0] is f and r[1][1] == 2 and len(r) == 2)
c = iter(lambda: 2, 2)
assert_eq((list(c), c.__reduce__()), ([], (iter, ((),))))
assert_false(hasattr(c, "__setstate__"))
e = assert_raises(TypeError, type(c).__reduce__, iter(s))
assert_eq(str(e), "descriptor '__reduce__' for 'callable_iterator' objects doesn't apply to a 'iterator' object")

# A callable that exhausts its own iterator: its result is discarded.
calls = []
def spam():
    calls.append(len(calls))
    if len(calls) > 1:
        return "stop"
    list(spam.iterator)
    return "more"
spam.iterator = iter(spam, "stop")
assert_raises(StopIteration, next, spam.iterator)
assert_eq((calls, spam.iterator.__reduce__()), ([0, 1], (iter, ((),))))
# The callable stays alive for the call even when the iterator drops it.
def once():
    if not holder:
        return 6
    del holder[:]
    list(it2)
    return 5
holder = [once]
it2 = iter(holder[0], 6)
del once
assert_raises(StopIteration, next, it2)
