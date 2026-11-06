# spec: PLS-315 19.3.35, 19.3.3, 13.16
# description: sum, any, all, list and tuple take a generator's items in
# order until it ends, any and all stop at the first item that decides,
# and what the generator raises reaches their caller.
from harness import *

def count(n):
    i = 0
    while i < n:
        yield i
        i += 1

assert sum(count(5)) == 10
assert sum(count(5), 100) == 110
assert sum(x / 10 for x in range(10)) == 4.5
assert sum((0.1 for _ in range(10)), 0.0) == 1.0
assert sum((x for x in [1, 2.5, 3]), 1) == 7.5
assert sum((x for x in [[1], [2]]), []) == [1, 2]
assert list(count(3)) == [0, 1, 2]
assert tuple(count(3)) == (0, 1, 2)
assert list(x * x for x in count(4)) == [0, 1, 4, 9]
assert tuple(count(0)) == ()
assert sum(count(0)) == 0

try:
    sum((x for x in 'ab'), '')
except TypeError as e:
    assert str(e) == "sum() can't sum strings [use ''.join(seq) instead]", str(e)
else:
    raise AssertionError('no TypeError')

# any and all stop early; the generator stays suspended until dropped.
log = []
def logged(items):
    try:
        for x in items:
            log.append(x)
            yield x
    finally:
        log.append('closed')

g = logged([0, 3, 0, 5])
assert any(g) is True
assert log == [0, 3]
del g
assert log == [0, 3, 'closed']
log.clear()
assert all(logged([1, 0, 1])) is False
assert log == [1, 0, 'closed']
log.clear()
assert any(logged([])) is False and all(logged([])) is True

# Delegation, and an exception from inside the generator.
def outer():
    yield 'a'
    yield from count(2)
    yield 'b'

assert list(outer()) == ['a', 0, 1, 'b']

def failing():
    yield 1
    raise KeyError('k')

try:
    list(failing())
except KeyError as e:
    assert e.args == ('k',)
else:
    raise AssertionError('no KeyError')

def stopping():
    yield 1
    raise StopIteration

try:
    tuple(stopping())
except RuntimeError as e:
    assert str(e) == 'generator raised StopIteration'
else:
    raise AssertionError('no RuntimeError')

# A generator that consumes itself is already running.
def itself():
    yield sum(me)

me = itself()
try:
    next(me)
except ValueError as e:
    assert str(e) == 'generator already executing'
else:
    raise AssertionError('no ValueError')

# A sum whose items have their own addition.
class Money:
    def __init__(self, n): self.n = n
    def __add__(self, other): return Money(self.n + (other.n if isinstance(other, Money) else other))
    __radd__ = __add__

assert sum(Money(i) for i in range(4)).n == 6
