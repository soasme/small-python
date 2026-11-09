# spec: PLS-315 7.4.1, 26, 27
# description: A class of __getitem__ alone iterates by calling it with
# 0, 1, 2, ... until an IndexError or StopIteration, in a for loop, a
# comprehension, list(), tuple(), sum(), sorted(), min(), set() and
# str.join, and through iter(); its end lasts, other exceptions
# propagate, and a __getitem__ of the wrong arity raises TypeError. With
# a __len__, reversed() calls it from len() - 1 down to 0, ending for good
# at an IndexError, StopIteration or any other exception, inside
# functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Seq:
    def __init__(self, n, end=IndexError): self.n = n; self.end = end
    def __getitem__(self, i):
        spin()
        log.append(i)
        if i >= self.n: raise self.end(i)
        return i * 10

class Bad:
    def __getitem__(self, i):
        if i == 2: raise KeyError(i)
        return i

class Arity:
    def __getitem__(self): return 0

class Sized:
    def __init__(self, n, fail=-1): self.n = n; self.fail = fail
    def __len__(self): return self.n
    def __getitem__(self, i):
        spin()
        if i == self.fail: raise KeyError(i)
        if i >= 2: raise IndexError(i)
        return i

class Words:
    def __getitem__(self, i):
        if i == 3: raise IndexError
        return "abc"[i]

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    out = []
    for x in Seq(3): out.append(x)
    out.append([x + 1 for x in Seq(2)])
    out += [list(Seq(2)), tuple(Seq(2, StopIteration)), sum(Seq(4)), sorted(Seq(3)), min(Seq(3)), max(Seq(2)),
            sorted(set(Seq(3))), "-".join(Words()), list(iter(Seq(1)))]
    it = iter(Seq(1))
    out += [next(it), error(lambda: next(it)), error(lambda: next(it))]
    out += [[x for x in it], list(it)]
    out += [error(lambda: list(Bad())), error(lambda: [x for x in Bad()]), error(lambda: list(Arity()))]
    bad = reversed(Sized(2, 0))
    out += [[x for x in reversed(Sized(2))], list(reversed(Sized(2))), list(reversed(Sized(3))), error(lambda: list(bad)), list(bad)]
    rev = []
    for x in reversed(Sized(2)): rev.append(x)
    out.append(rev)
    for_bad = []
    try:
        for x in Bad(): for_bad.append(x)
    except KeyError as e:
        for_bad.append(("KeyError", e.args))
    out.append(for_bad)
    out.append(list(log))
    return out

expected = [0, 10, 20, [1, 11], [0, 10], (0, 10), 60, [0, 10, 20], 0, 10, [0, 10, 20], 'a-b-c', [0], 0,
            ('StopIteration', ''), ('StopIteration', ''), [], [], ('KeyError', '2'), ('KeyError', '2'),
            ('TypeError', 'Arity.__getitem__() takes 1 positional argument but 2 were given'), 
            [1, 0], [1, 0], [], ('KeyError', '0'), [], [1, 0], [0, 1, ('KeyError', (2,))],
            [0, 1, 2, 3, 0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2, 3, 4, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 0, 1, 2, 3, 0, 1, 0, 1]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
