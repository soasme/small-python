# spec: PLS-315 27.1.2, 27.1.7
# description: A sequence iterator whose __getitem__ raises an exception
# other than IndexError or StopIteration propagates it and tries the same
# index on its next step, through next() or a loop, while any exception
# ends a reversed iterator; with __getitem__ calling others or not, inside
# functions as at module level.
from harness import *

class Flaky:
    fail = 0
    def __getitem__(self, i):
        for _ in range(1): pass
        if Flaky.fail:
            Flaky.fail -= 1
            raise KeyError(i)
        if i > 2: raise IndexError(i)
        return i

class Quick(Flaky):
    def __getitem__(self, i):
        if Flaky.fail:
            Flaky.fail -= 1
            raise KeyError(i)
        return [0, 1, 2][i]

class Sized(Flaky):
    def __len__(self): return 3

def steps(make):
    out = []
    it = make(); Flaky.fail = 1
    try:
        next(it)
    except KeyError as e:
        out.append(("next", e.args[0]))
    out.append(list(it))
    it = make(); next(it); Flaky.fail = 1
    try:
        for x in it: out.append(x)
    except KeyError as e:
        out.append(("loop", e.args[0]))
    out.append([*it])
    return out

def calls():
    return [steps(lambda: iter(Flaky())), steps(lambda: iter(Quick())), steps(lambda: reversed(Sized()))]

expected = [[("next", 0), [0, 1, 2], ("loop", 1), [1, 2]],
            [("next", 0), [0, 1, 2], ("loop", 1), [1, 2]],
            [("next", 2), [], ("loop", 1), []]]
assert_eq(calls(), expected)
assert_eq(calls(), expected)
it = iter(Flaky()); Flaky.fail = 1
assert_raises(KeyError, next, it)
assert_eq([next(it), next(it, "d"), list(it), next(it, "e")], [0, 1, [2], "e"])
