# spec: PLS-315 13.16, 13.16.3
# description: Generators: yield, send, yield from, and return values.
from harness import *


r = []

def make_numbers():
    yield 1
    yield 2
    r.append(42)
    yield 3

for a in make_numbers():
    r.append(a)

assert r == [1, 2, 42, 3]

r = list(x for x in [1, 2, 3])
assert r == [1, 2, 3]

r = list(y := x + 1 for x in [1, 2, 3])
assert r == [2, 3, 4]

def g2(x):
    x = yield x
    yield x + 5
    yield x + 7

i = g2(23)
assert 23 == next(i)
assert 15 == i.send(10)
assert 17 == i.send(10)


def g3():
    yield 23
    yield from make_numbers()
    yield 44
    yield from make_numbers()

r = list(g3())
# print(r)
assert r == [23, 1, 2, 3, 44, 1, 2, 3]

def g4():
    yield
    yield 2,

r = list(g4())
assert r == [None, (2,)]


def catch_exception():
    try:
        yield 1
    except ValueError:
        yield 2
        yield 3


g = catch_exception()
assert next(g) == 1

assert g.throw(ValueError, ValueError(), None) == 2
assert next(g) == 3

g = catch_exception()
assert next(g) == 1

with assert_raises(KeyError):
    assert g.throw(KeyError, KeyError(), None) == 2


r = []
def p(a, b, c):
    # print(a, b, c)
    r.append(a)
    r.append(b)
    r.append(c)


def g5():
    p('a', (yield 2), (yield 5))
    yield 99

g = g5()
g.send(None)
g.send(66)
# g.send(88)
l = list(g)
# print(r)
# print(l)
assert l == [99]
assert r == ['a', 66, None]

def binary(n):
    if n <= 1:
        return 1
    l = yield from binary(n - 1)
    r = yield from binary(n - 1)
    return l + 1 + r

with assert_raises(StopIteration):
    try:
        next(binary(5))
    except StopIteration as stop_iter:
        assert stop_iter.value == 31
        assert stop_iter.args[0] == 31
        raise

class SpamException(Exception):
    pass

l = []

def writer():
    while True:
        try:
            w = (yield)
        except SpamException:
            l.append('***')
        else:
            l.append(f'>> {w}')

def wrapper(coro):
    yield from coro

w = writer()
wrap = wrapper(w)
wrap.send(None)  # "prime" the coroutine
for i in [0, 1, 2, 'spam', 4]:
    if i == 'spam':
        wrap.throw(SpamException)
    else:
        wrap.send(i)

assert l == ['>> 0', '>> 1', '>> 2', '***', '>> 4']

def a():
  yield

g = a()

next(g)
assert_raises(TypeError, g.throw, TypeError)
assert_raises(StopIteration, next, g)
assert_raises(TypeError, g.throw, TypeError)

def a():
    assert g.gi_running
    try:
        yield
    except:
        assert g.gi_running


g = a()
next(g)
assert_raises(StopIteration, g.throw, TypeError)

g = a()
next(g)
g.close()

it = iter([1,2,3,4])

def a():
    yield from it

g = a()
assert next(g) == 1
assert g.gi_yieldfrom is it
assert list(g) == [2,3,4]
assert g.gi_yieldfrom is None

# close() through yield from: an error getting the subiterator's close is
# unraisable and the delegation ends as if there were no close; throw() and
# send() propagate theirs, and an exception from close itself propagates.
class BrokenAttrs:
    def __iter__(self): return self
    def __next__(self): return 1
    def __getattr__(self, name): 1 / 0
def delegator(it):
    yield from it
d = delegator(BrokenAttrs())
next(d)
assert_eq(d.close(), None)
assert_eq(d.gi_frame, None)
# throw() raises the lookup error without resuming the delegator.
d = delegator(BrokenAttrs())
next(d)
assert_raises(ZeroDivisionError, d.throw, KeyError)
assert_eq((d.gi_suspended, next(d)), (True, 1))
d = delegator(BrokenAttrs())
next(d)
assert_raises(ZeroDivisionError, d.send, 1)
class NoClose:
    def __iter__(self): return self
    def __next__(self): return 1
d = delegator(NoClose())
next(d)
assert_eq(d.close(), None)
class CloseRaises(NoClose):
    def close(self): raise KeyError("closing")
d = delegator(CloseRaises())
next(d)
assert_eq(str(assert_raises(KeyError, d.close)), "'closing'")

# Yields inside every expression form suspend in evaluation order.
class Key:
    def __getitem__(self, key): return key
def forms():
    a = (yield 1) if (yield 2) else (yield 3)
    b = (n := (yield 4))
    c = f"{(yield 5)!r:>{(yield 6)}}"
    d = {(yield 7): (yield 8), **(yield 9)}
    e = [*(yield 10), (yield 11)]
    h = {(yield 12), *(yield 13)}
    i = ((yield 14), (yield 15))
    j = (yield 16)[(yield 17):(yield 18)]
    k = (yield 19).real
    l = not (yield 20)
    m = (yield 21) < (yield 22) < (yield 23)
    o = (yield 24) or (yield 25)
    p = lambda q=(yield 26): q
    s = (yield 28)(*(yield 29), **(yield 30))
    t = Key()[*(yield 31)]
    yield (a, b, n, c, d, e, h, i, j, k, l, m, o, p(), s, t)
sends = {2: 1, 1: "A", 4: "N", 5: 5, 6: 3, 7: "k", 8: "v", 9: {"z": 1}, 10: [1], 11: 2, 12: 3, 13: [4], 14: 1, 15: 2,
         16: "abcdef", 17: 1, 18: 3, 19: 2, 20: 0, 21: 1, 22: 2, 23: 3, 24: 0, 25: "or", 26: "Q", 28: max, 29: [1, 2], 30: {},
         31: [5, 6]}
order, generator = [], forms()
value = next(generator)
while not isinstance(value, tuple):
    order.append(value)
    value = generator.send(sends[value])
assert_eq(order, [2, 1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 28, 29, 30, 31])
assert_eq(value, ("A", "N", "N", "  5", {"k": "v", "z": 1}, [1, 2], {3, 4}, (1, 2), "bc", 2, True, True, "or", "Q", 2, (5, 6)))

# Targets suspend after the value: attributes, items and augmented forms.
class Box:
    x = 0
class Manager:
    def __enter__(self): return "entered"
    def __exit__(self, *args): return False
def targets(box, store):
    (yield).x = (yield)
    box.x += (yield)
    (yield).x += 1
    store[(yield)] = (yield)
    with (yield) as w:
        yield w
box, store = Box(), {}
generator = targets(box, store)
next(generator)
for sent in (5, box, 2, box, 1, "k", Manager()):
    last = generator.send(sent)
assert_eq((last, box.x, store), ("entered", 8, {"k": 1}))
