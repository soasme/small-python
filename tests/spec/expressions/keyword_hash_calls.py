# spec: PLS-315 13.3.4, 13.2.3, 26.1.1, 26.2
# description: A call's ** merges a dict keeping its keys' stored hashes:
# keyword names that are instances of a str subclass with a Python
# __hash__ and __eq__ are compared only with a merged name of equal hash,
# a duplicate raising TypeError with no hash; a function's **kw, dict()
# and frozendict() then hash each name once, while a dict or frozendict
# subclass, dict.update(), dict.__init__ and a display's ** merge them
# without hashing. A name's __hash__ that raises, or returns no int, when
# **kw stores it fails the call, and the keywords after a hashed one bind
# in turn. Inside functions as at module level.
from harness import *

log = []

class Name(str):
    def __hash__(self):
        log.append("hash")
        return str.__hash__(self)
    def __eq__(self, other):
        log.append("eq")
        return str.__eq__(self, other)

class D(dict): pass
class F(frozendict): pass

def f(**kw): return kw
def g(a=None, **kw): return a

def t(call):
    a, b = {Name("a"): 1}, {Name("b"): 2}
    del log[:]
    try:
        r = call(a, b)
        r = [(str(k), v) for k, v in r.items()] if isinstance(r, (dict, frozendict)) else r
    except TypeError as e:
        r = "TypeError: " + str(e)
    return r, log[:]

def init(x, a, b):
    dict.__init__(x, **a, **b)
    return x

def update(x, a, b):
    x.update(**a, **b)
    return x

def results():
    return [t(lambda a, b: f(**a)), t(lambda a, b: f(**a, **b)), t(lambda a, b: f(z=0, **a)), t(lambda a, b: f(a=0, **a)),
            t(lambda a, b: f(**a, **{Name("a"): 3})), t(lambda a, b: dict(**a, **b)), t(lambda a, b: dict([("p", 0)], **a)),
            t(lambda a, b: frozendict(**a)), t(lambda a, b: D(**a, **b)), t(lambda a, b: F(**a)),
            t(lambda a, b: update({}, a, b)), t(lambda a, b: init({}, a, b)), t(lambda a, b: {**a, **b}),
            t(lambda a, b: {"a": 0, **a}), t(lambda a, b: dict(a=0, **a)), t(lambda a, b: g(**b))]

expected = [([('a', 1)], ['hash']), ([('a', 1), ('b', 2)], ['hash', 'hash']), ([('z', 0), ('a', 1)], ['hash']),
            ("TypeError: __main__.f() got multiple values for keyword argument 'a'", ['eq']),
            ("TypeError: __main__.f() got multiple values for keyword argument 'a'", ['hash', 'eq']),
            ([('a', 1), ('b', 2)], ['hash', 'hash']), ([('p', 0), ('a', 1)], ['hash']), ([('a', 1)], ['hash']),
            ([('a', 1), ('b', 2)], []), ([('a', 1)], []), ([('a', 1), ('b', 2)], []), ([('a', 1), ('b', 2)], []),
            ([('a', 1), ('b', 2)], []), ([('a', 1)], ['eq']),
            ("TypeError: dict() got multiple values for keyword argument 'a'", ['eq']), (None, ['eq', 'hash'])]

class Late(str):
    def __hash__(self):
        for _ in range(2): pass
        log.append("late")
        if len(log) == 1: return str.__hash__(self)
        if str(self) == "r": raise LookupError(str(self))
        if str(self) == "t": raise TypeError(str(self))
        return "no int" if str(self) == "s" else str.__hash__(self)
    __eq__ = str.__eq__

def late(call):
    del log[:]
    try:
        r = call()
        r = sorted((str(k), v) for k, v in r.items()) if isinstance(r, dict) else r
    except (LookupError, TypeError) as e:
        r = type(e).__name__ + ": " + str(e)
    return r, log[:]

def h(a=None, *, c=0, **kw): return a, c, kw

def hashed():
    return [late(lambda: f(**{Late("r"): 1})), late(lambda: f(**{Late("s"): 1})), late(lambda: f(**{Late("t"): 1})), late(lambda: f(**{Late("q"): 1})),
            late(lambda: h(**{Late("q"): 1}, c=2)[1:]), late(lambda: h(**{Late("q"): 1}, a=3)[0]),
            late(lambda: h(**{Late("q"): 1}, **{Name("c"): 4})[1])]

expected_hashed = [('LookupError: r', ['late', 'late']), ("TypeError: cannot use 'Late' as a dict key (__hash__ method should return an integer)", ['late', 'late']), ("TypeError: cannot use 'Late' as a dict key (t)", ['late', 'late']), ([('q', 1)], ['late', 'late']), ((2, {'q': 1}), ['late', 'late']), (3, ['late', 'late']), (4, ['late', 'hash', 'late', 'eq', 'eq'])]

def main():
    return results(), hashed()

# The functions' first calls, which run in C, bind as later ones.
assert_eq(hashed(), expected_hashed)

assert_eq(main(), (expected, expected_hashed))
assert_eq((results(), hashed()), (expected, expected_hashed))
