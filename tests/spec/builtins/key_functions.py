# spec: PLS-315 25.1.4, 19.3.34, 19.3.26
# description: A sort by key calls the key once per item, in order, while
# the list is empty; sorts stably in either direction; and leaves the list
# as it was when a key raises, or raises when a key changed it. min and max
# compare each item's key with the best one's as they take it, keeping the
# first of equal ones.
from harness import *

calls = []
def key(x):
    calls.append(x)
    return -x

def sorts():
    xs = [3, 1, 2]
    xs.sort(key=key)
    return xs, sorted((5, 4, 6), key=key), calls

assert sorts() == ([3, 2, 1], [6, 5, 4], [3, 1, 2, 5, 4, 6])

def stable():
    pairs = [(1, 'b'), (0, 'a'), (1, 'a'), (0, 'b')]
    first = lambda p: p[0]
    return sorted(pairs, key=first), sorted(pairs, key=first, reverse=True)

assert stable() == ([(0, 'a'), (0, 'b'), (1, 'b'), (1, 'a')],
                    [(1, 'b'), (1, 'a'), (0, 'a'), (0, 'b')])

def empty_while_sorting():
    seen = []
    xs = [2, 1, 3]
    def peek(x):
        seen.append(len(xs))
        return x
    xs.sort(key=peek, reverse=False)
    return xs, seen, sorted('', key=peek), sorted(range(3), key=lambda v: -v)

assert empty_while_sorting() == ([1, 2, 3], [0, 0, 0], [], [2, 1, 0])

def raising():
    xs = [3, 2, 1]
    try:
        xs.sort(key=lambda x: 1 // (x - 2))
    except ZeroDivisionError:
        return xs

assert raising() == [3, 2, 1]

def modified():
    xs = [2, 1]
    def grow(x):
        xs.append(x)
        return x
    try:
        xs.sort(key=grow)
    except ValueError as e:
        return str(e), xs

assert modified() == ('list modified during sort', [1, 2])

def changed_then_raising():
    xs = [2, 1]
    def bad(x):
        xs.append(x)
        raise KeyError(x)
    try:
        xs.sort(key=bad)
    except KeyError as e:
        return e.args, xs

assert changed_then_raising() == ((2,), [2, 1])

def failing_comparison():
    try:
        sorted([1, 'a'], key=lambda v: v)
    except TypeError as e:
        return str(e)

assert failing_comparison() == "'<' not supported between instances of 'str' and 'int'"

def reverse_raising():
    class Bad:
        def __bool__(self): raise KeyError('bool')
    try:
        [1].sort(key=lambda v: v, reverse=Bad())
    except KeyError as e:
        return e.args

assert reverse_raising() == ('bool',)

def extremes():
    log = []
    class K:
        def __init__(self, v): self.v = v
        def __gt__(self, other):
            log.append(('gt', self.v, other.v))
            return self.v > other.v
        def __lt__(self, other):
            log.append(('lt', self.v, other.v))
            return self.v < other.v
    def key(v):
        log.append(('key', v))
        return K(v % 3)
    best = max([1, 2, 5, 3], key=key), min(4, 3, 6, key=key)
    return best, log

assert extremes() == ((2, 3), [('key', 1), ('key', 2), ('gt', 2, 1), ('key', 5), ('gt', 2, 2), ('key', 3), ('gt', 0, 2),
                               ('key', 4), ('key', 3), ('lt', 0, 1), ('key', 6), ('lt', 0, 0)])

def empty():
    out = []
    for f in (max, min):
        try:
            f([], key=lambda v: v)
        except ValueError as e:
            out.append(str(e))
    return out, max([], key=lambda v: v, default='none'), min(iter('ba'), key=lambda v: v)

assert empty() == (['max() iterable argument is empty', 'min() iterable argument is empty'], 'none', 'a')

def failing_key():
    seen = []
    def key(v):
        seen.append(v)
        return 1 // v
    try:
        max([2, 0, 1], key=key)
    except ZeroDivisionError:
        return seen

assert failing_key() == [2, 0]
