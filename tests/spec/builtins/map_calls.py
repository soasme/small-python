# spec: PLS-315 27.1.6, 19.3.3, 19.3.35
# description: A map calls its function with the next item of each
# iterable, left to right, once per item a loop or a consumer takes; a
# StopIteration from the function ends it, and other exceptions reach the
# caller. A bound method, or a callable instance's __call__, is called with
# its self first.
from harness import *

log = []
def logged(*args):
    log.append(args)
    return sum(args)

def loops():
    out = []
    for x in map(logged, [1, 2], (10, 20, 30)):
        out.append(x)
    return out

assert loops() == [11, 22]
assert log == [(1, 10), (2, 20)]

def consumers():
    sq = lambda v: v * v
    return (list(map(sq, range(4))), tuple(map(sq, [])), sum(map(sq, range(4))),
            any(map(sq, [0, 0, 2])), all(map(sq, [1, 0])), set(map(sq, [1, -1])),
            sorted(map(sq, [3, -1])), '-'.join(map(lambda s: s * 2, 'ab')),
            frozenset(map(sq, [2])))

assert consumers() == ([0, 1, 4, 9], (), 14, True, False, {1}, [1, 9], 'aa-bb', frozenset({4}))

def stop(v):
    if v == 2:
        raise StopIteration
    return v

def stopping():
    out = []
    for x in map(stop, [1, 2, 3]):
        out.append(x)
    return out, list(map(stop, [1, 2, 3]))

assert stopping() == ([1], [1])

def raising():
    seen = []
    def f(v):
        seen.append(v)
        return 1 // v
    try:
        list(map(f, [1, 0, 2]))
    except ZeroDivisionError:
        return seen

assert raising() == [1, 0]

def exhausted():
    m = map(lambda v: v, [5])
    return [x for x in m], list(m)

assert exhausted() == ([5], [])

def strict():
    try:
        for x in map(lambda a, b: a, [1], [1, 2], strict=True):
            pass
    except ValueError as e:
        return str(e)

assert strict() == 'map() argument 2 is longer than argument 1'

# A stopped consumer leaves the rest of the iterable untaken.
items = iter([0, 3, 0, 5])
assert any(map(lambda v: v, items)) is True
assert list(items) == [0, 5]

class Scale:
    def __init__(self, k): self.k = k
    def times(self, v, w=1): return self.k * v * w
    def __call__(self, v):
        if v == 3:
            raise StopIteration
        return self.k + v

class Narrow:
    def __call__(self): pass

def bound():
    s = Scale(10)
    try:
        list(map(Narrow(), [1]))
    except TypeError as e:
        narrow = str(e)
    return (list(map(s.times, [1, 2], [3, 4])), [x for x in map(s, [1, 2, 3, 4])], sum(map(Scale(1), [5, 3])),
            list(map(s.times, [])), narrow)

assert bound() == ([30, 80], [11, 12], 6, [], 'Narrow.__call__() takes 1 positional argument but 2 were given')
