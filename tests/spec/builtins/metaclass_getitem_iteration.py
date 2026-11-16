# spec: PLS-315 7.7.2, 27.1.7
# description: A class whose metaclass defines a Python __getitem__, which
# may loop, iterates by it for list(), tuple(), sum(), sorted(), in, zip()
# and a comprehension, and reverses by it and the metaclass's __len__;
# an IndexError ends the items, another exception propagates, and the
# class's own __class_getitem__ serves only subscription. Inside
# functions as at module level.
from harness import *

log = []
class Meta(type):
    def __len__(cls): return 3
    def __getitem__(cls, i):
        for _ in range(2): pass
        log.append(i)
        if i >= 3: raise IndexError(i)
        if i == cls.bad: raise LookupError(i)
        return i * 10
class Seq(metaclass=Meta): bad = -1
class Bad(metaclass=Meta): bad = 1
class Own(metaclass=Meta):
    bad = -1
    def __class_getitem__(cls, i): return "cg"
def t(f):
    try: r = f()
    except Exception as e: r = type(e).__name__ + ": " + str(e)
    out = (r, log[:]); del log[:]; return out
def results():
    return [t(lambda: list(reversed(Seq))), t(lambda: list(Seq)), t(lambda: [x for x in Seq]), t(lambda: sum(Seq)),
            t(lambda: list(reversed(Bad))), t(lambda: list(Bad)), t(lambda: 20 in Seq), t(lambda: list(Own)),
            t(lambda: tuple(reversed(Own))), t(lambda: sorted(Seq, reverse=True)), t(lambda: dict(zip(Seq, reversed(Seq)))),
            t(lambda: (Own[0], Seq[1]))]

expected = [([20, 10, 0], [2, 1, 0]), ([0, 10, 20], [0, 1, 2, 3]), ([0, 10, 20], [0, 1, 2, 3]), (30, [0, 1, 2, 3]),
            ('LookupError: 1', [2, 1]), ('LookupError: 1', [0, 1]), (True, [0, 1, 2]), ([0, 10, 20], [0, 1, 2, 3]),
            ((20, 10, 0), [2, 1, 0]), ([20, 10, 0], [0, 1, 2, 3]), ({0: 20, 10: 10, 20: 0}, [0, 2, 1, 1, 2, 0, 3]),
            ((0, 10), [0, 1])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
