# spec: PLS-315 13.3.4, 26.1.1
# description: A call's first ** of a dict, or of a frozendict or dict
# subclass, merges into keywords that hold none without comparing its
# keys, which are distinct, as a display's ** does; its names are compared
# only as the callee's ** parameter, dict() or frozendict() stores them.
# A ** after other keywords compares each name of equal hash with those
# gathered, then as it stores it. Inside functions and generators as at
# module level.
from harness import *

log = []

class Name(str):
    def __hash__(self): return 7
    def __eq__(self, other):
        for _ in range(2): pass
        log.append((str(self), str(other)))
        return str.__eq__(self, other)

class Keywords(dict): pass

def f(**kw): return sorted(kw.values())
def g(p, **kw): return sorted(kw.values())

def logged(thunk):
    del log[:]
    thunk()
    return list(log)

def results():
    k = {Name("a"): 1, Name("b"): 2, Name("c"): 3}
    sub = Keywords(k)
    frozen = frozendict(k)
    return [logged(lambda: f(**k)), logged(lambda: f(**sub)), logged(lambda: f(**frozen)),
            logged(lambda: f(**k, **{})), logged(lambda: g(1, **k)), logged(lambda: dict(**k)),
            logged(lambda: f(**k, x=1)), logged(lambda: f(x=1, **k)), logged(lambda: {**k})]

stored = [("a", "b"), ("a", "c"), ("b", "c")]
gathered = [("a", "b"), ("a", "b"), ("a", "c"), ("b", "c"), ("a", "c"), ("b", "c")]
# g's parameter p is compared with each name before it is stored.
expected = [stored] * 4 + [[("a", "p"), ("b", "p"), ("a", "b"), ("c", "p"), ("a", "c"), ("b", "c")]] + [stored] * 2 + [gathered + stored, []]

assert_eq(results(), expected)

def inside():
    return results()
assert_eq(inside(), expected)

def gen():
    yield results()
assert_eq(next(gen()), expected)
