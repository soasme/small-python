# spec: PLS-315 19.3.35, 19.3.3, 19.3.34, 19.3.26, 27.1.4, 27.1.5, 13.16
# description: sum, any, all, min, max, list and tuple take a generator's
# items in order until it ends, any and all stop at the first item that
# decides, min and max compare each item with the best before the next,
# an enumerate or filter over a generator takes its items one at a time,
# set and frozenset stop at an unhashable item, and what the generator
# raises reaches their caller.
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

# set, frozenset, sorted and str.join take all the items first.
assert set(count(4)) == {0, 1, 2, 3}
assert frozenset(x % 2 for x in range(5)) == frozenset({0, 1})
assert sorted(x % 3 for x in range(6)) == [0, 0, 1, 1, 2, 2]
assert '-'.join(str(i) for i in count(3)) == '0-1-2'
assert ''.join(c for c in '') == ''

def joined():
    return ', '.join(str(x) for x in count(3)), sorted(count(2)), set(x for x in 'aa')

assert joined() == ('0, 1, 2', [0, 1], {'a'})

taken = []
def mixed():
    for x in ['a', 1, 'b']:
        taken.append(x)
        yield x

try:
    ''.join(mixed())
except TypeError as e:
    assert str(e) == 'sequence item 1: expected str instance, int found', str(e)
else:
    raise AssertionError('no TypeError')
assert taken == ['a', 1, 'b'], taken

try:
    set([] for _ in range(1))
except TypeError as e:
    assert str(e) == "cannot use 'list' as a set element (unhashable type: 'list')", str(e)
else:
    raise AssertionError('no TypeError')

# min and max compare each item with the best so far as it arrives, the
# new item on the left, and keep the first of equal items.
order = []
class Ranked:
    def __init__(self, n, name): self.n, self.name = n, name
    def __lt__(self, other): order.append(("<", self.name, other.name)); return self.n < other.n
    def __gt__(self, other): order.append((">", self.name, other.name)); return self.n > other.n
def ranked():
    for n, name in ((1, "a"), (3, "b"), (3, "c"), (0, "d")):
        order.append(name)
        yield Ranked(n, name)
assert max(ranked()).name == "b"
assert order == ["a", "b", (">", "b", "a"), "c", (">", "c", "b"), "d", (">", "d", "b")], order
order.clear()
assert min(ranked()).name == "d"
assert order == ["a", "b", ("<", "b", "a"), "c", ("<", "c", "a"), "d", ("<", "d", "a")], order
assert (max(count(4)), min(x - 1 for x in count(3))) == (3, -1)
for f, name in ((max, "max"), (min, "min")):
    try:
        f(count(0))
    except ValueError as e:
        assert str(e) == name + "() iterable argument is empty", str(e)
    else:
        raise AssertionError("no ValueError")
try:
    max(x for x in [1, "a"])
except TypeError as e:
    assert str(e) == "'>' not supported between instances of 'str' and 'int'", str(e)
else:
    raise AssertionError("no TypeError")

# enumerate and filter over a generator, in loops and consumers: each item
# is numbered or tested as the generator yields it, a StopIteration from a
# filter's function ends that pass only, and an error reaches the caller.
seen = []
def tracked():
    for x in [0, 1, "", 3]:
        seen.append(("yield", x))
        yield x
def loud(x):
    seen.append(("test", x))
    return x
def adapters():
    out = []
    for i, x in enumerate(tracked(), 10):
        out.append((i, x))
    for x in filter(None, tracked()):
        out.append(x)
    out.append(sum(filter(None, tracked())))
    out.append(list(enumerate(tracked())))
    out.append(max(filter(None, tracked())))
    return out
assert adapters() == [(10, 0), (11, 1), (12, ""), (13, 3), 1, 3, 4,
                      [(0, 0), (1, 1), (2, ""), (3, 3)], 3]
seen.clear()
assert list(filter(loud, tracked())) == [1, 3]
assert seen == [("yield", 0), ("test", 0), ("yield", 1), ("test", 1), ("yield", ""), ("test", ""), ("yield", 3), ("test", 3)], seen
def stopping(x):
    if x == 1: raise StopIteration
    return True
def partial():
    source = tracked()
    taken = filter(stopping, source)
    first = [x for x in taken]
    return first, next(source), list(taken)
assert partial() == ([0], "", [3])
def broken():
    yield 1
    raise KeyError("k")
def raising():
    try:
        for x in enumerate(broken()): pass
    except KeyError as e:
        return e.args
assert raising() == ("k",)
def native_tests():
    lists = (iter(x) for x in [[1], [], [2]])
    taken = filter(next, lists)
    first = [x for x in taken]
    try:
        for x in filter(int, (s for s in ["1", "x"])): pass
    except ValueError as e:
        return len(first), len(list(taken)), str(e)
assert native_tests() == (1, 1, "invalid literal for int() with base 10: 'x'")
def unhashable_first():
    taken = []
    def items():
        yield []
        taken.append("after")
        yield 1
    out = []
    for build in (set, frozenset):
        try: build(items())
        except TypeError as e: out.append(str(e))
    return out, taken
assert unhashable_first() == (["cannot use 'list' as a set element (unhashable type: 'list')"] * 2, [])
