# spec: PLS-315 13.3.4, 13.2.3, 26.1.1, 26.2
# description: A call's ** merges a dict keeping its keys' stored hashes:
# keyword names that are instances of a str subclass with a Python
# __hash__ and __eq__ are compared only with a merged name of equal hash,
# a duplicate raising TypeError with no hash; a function's **kw, dict()
# and frozendict() then hash each name once, while a dict or frozendict
# subclass, dict.update(), dict.__init__ and a display's ** merge them
# without hashing. Inside functions as at module level.
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

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
