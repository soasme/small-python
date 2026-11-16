# spec: PLS-315 27.1.1, 27.1.5
# description: An explicit __next__ of a map or filter iterator over a
# Python function, called bound, through its type given the iterator, as
# a stored method-wrapper or by super() in a subclass, calls that
# function, which may loop, for its item as next() does, in a display
# too; the function's exception propagates, an exhausted iterator raises
# StopIteration, and a type's __next__ given another type's iterator
# raises TypeError. Inside functions as at module level.
from harness import *

log = []

def sq(x):
    for _ in range(2): pass
    log.append(x)
    if x == 9: raise LookupError(x)
    return x * x

def odd(x):
    log.append(("odd", x))
    return x % 2

class M(map):
    def __next__(self): return super().__next__() + 1

def t(f):
    try:
        r = f()
    except StopIteration as e:
        r = ("StopIteration", e.args)
    except Exception as e:
        r = type(e).__name__ + ": " + str(e)
    out = (r, log[:])
    del log[:]
    return out

def results():
    m, f = map(sq, [1, 2, 9]), filter(odd, [2, 3])
    wrapper, shown = map(sq, [4]).__next__, map(sq, [7]).__next__
    return [t(lambda: m.__next__()), t(lambda: map.__next__(m)), t(lambda: m.__next__()), t(lambda: m.__next__()),
            t(lambda: f.__next__()), t(lambda: filter.__next__(f)), t(lambda: map.__next__(f)), t(wrapper), t(wrapper),
            t(lambda: list(M(sq, [5, 6]))), t(lambda: next(M(sq, [9]))), t(lambda: (0, shown(), 1))]

expected = [(1, [1]), (4, [2]), ('LookupError: 9', [9]), (('StopIteration', ()), []), (3, [('odd', 2), ('odd', 3)]),
            (('StopIteration', ()), []),
            ("TypeError: descriptor '__next__' requires a 'map' object but received a 'filter'", []), (16, [4]),
            (('StopIteration', ()), []), ([26, 37], [5, 6]), ('LookupError: 9', [9]), ((0, 49, 1), [7])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
