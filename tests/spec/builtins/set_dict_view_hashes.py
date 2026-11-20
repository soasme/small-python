# spec: PLS-315 26.3.1, 26.3.2, 13.2.2
# description: set(), frozenset(), set.update(), a set display and
# set.union() of a dict's or frozendict's keys, values or items view hash
# each key, value or (key, value) pair in order by its Python __hash__,
# comparing equal hashes by __eq__; a __hash__'s error propagates; and so
# inside a generator.
from harness import assert_eq

log = []
class H:
    def __init__(self, n, fail=False): self.n, self.fail = n, fail
    def __repr__(self): return "H%s" % self.n
    def __hash__(self):
        for _ in (): pass
        log.append(("hash", self.n))
        if self.fail: raise KeyError("hash")
        return self.n % 2
    def __eq__(self, o):
        for _ in (): pass
        log.append(("eq", self.n, getattr(o, "n", o)))
        return isinstance(o, H) and o.n % 2 == self.n % 2
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    if isinstance(r, (set, frozenset)): r = sorted(map(repr, r))
    return r, log[:]
CALLS = {}
for maker in (dict, frozendict):
    d = maker({H(1): H(3), H(2): H(4), 5: H(5)})
    bad = maker({1: H(9, True)})
    for view in ("keys", "values", "items"):
        CALLS[(maker.__name__, view, "set")] = (lambda d, view: lambda: set(getattr(d, view)()))(d, view)
        CALLS[(maker.__name__, view, "frozenset")] = (lambda d, view: lambda: frozenset(getattr(d, view)()))(d, view)
        CALLS[(maker.__name__, view, "update")] = (lambda d, view: lambda: (lambda s: (s.update(getattr(d, view)()), s)[1])(set()))(d, view)
        CALLS[(maker.__name__, view, "display")] = (lambda d, view: lambda: {*getattr(d, view)()})(d, view)
        CALLS[(maker.__name__, view, "union")] = (lambda d, view: lambda: set().union(d.keys(), getattr(d, view)()))(d, view)
    CALLS[(maker.__name__, "bad", "values")] = (lambda bad: lambda: set(bad.values()))(bad)
    CALLS[(maker.__name__, "bad", "items")] = (lambda bad: lambda: frozenset(bad.items()))(bad)
same = {H(1): 0, H(3): 0}
CALLS[("dict", "same", "keys")] = lambda: set(same.keys())

CASES = {
    ('dict', 'keys', 'set'): (['5', 'H1', 'H2'], [('hash', 1), ('hash', 2)]),
    ('dict', 'keys', 'frozenset'): (['5', 'H1', 'H2'], [('hash', 1), ('hash', 2)]),
    ('dict', 'keys', 'update'): (['5', 'H1', 'H2'], [('hash', 1), ('hash', 2)]),
    ('dict', 'keys', 'display'): (['5', 'H1', 'H2'], [('hash', 1), ('hash', 2)]),
    ('dict', 'keys', 'union'): (['5', 'H1', 'H2'], [('hash', 1), ('hash', 2), ('hash', 1), ('hash', 2)]),
    ('dict', 'values', 'set'): (['H3', 'H4'], [('hash', 3), ('hash', 4), ('hash', 5), ('eq', 3, 5)]),
    ('dict', 'values', 'frozenset'): (['H3', 'H4'], [('hash', 3), ('hash', 4), ('hash', 5), ('eq', 3, 5)]),
    ('dict', 'values', 'update'): (['H3', 'H4'], [('hash', 3), ('hash', 4), ('hash', 5), ('eq', 3, 5)]),
    ('dict', 'values', 'display'): (['H3', 'H4'], [('hash', 3), ('hash', 4), ('hash', 5), ('eq', 3, 5)]),
    ('dict', 'values', 'union'): (['5', 'H1', 'H2'], [('hash', 1), ('hash', 2), ('hash', 3), ('eq', 1, 3), ('hash', 4), ('eq', 2, 4), ('hash', 5), ('eq', 1, 5)]),
    ('dict', 'items', 'set'): (['(5, H5)', '(H1, H3)', '(H2, H4)'], [('hash', 1), ('hash', 3), ('hash', 2), ('hash', 4), ('hash', 5)]),
    ('dict', 'items', 'frozenset'): (['(5, H5)', '(H1, H3)', '(H2, H4)'], [('hash', 1), ('hash', 3), ('hash', 2), ('hash', 4), ('hash', 5)]),
    ('dict', 'items', 'update'): (['(5, H5)', '(H1, H3)', '(H2, H4)'], [('hash', 1), ('hash', 3), ('hash', 2), ('hash', 4), ('hash', 5)]),
    ('dict', 'items', 'display'): (['(5, H5)', '(H1, H3)', '(H2, H4)'], [('hash', 1), ('hash', 3), ('hash', 2), ('hash', 4), ('hash', 5)]),
    ('dict', 'items', 'union'): (['(5, H5)', '(H1, H3)', '(H2, H4)', '5', 'H1', 'H2'], [('hash', 1), ('hash', 2), ('hash', 1), ('hash', 3), ('hash', 2), ('hash', 4), ('hash', 5)]),
    ('dict', 'bad', 'values'): (('KeyError', "'hash'"), [('hash', 9)]),
    ('dict', 'bad', 'items'): (('KeyError', "'hash'"), [('hash', 9)]),
    ('frozendict', 'keys', 'set'): (['5', 'H1', 'H2'], [('hash', 1), ('hash', 2)]),
    ('frozendict', 'keys', 'frozenset'): (['5', 'H1', 'H2'], [('hash', 1), ('hash', 2)]),
    ('frozendict', 'keys', 'update'): (['5', 'H1', 'H2'], [('hash', 1), ('hash', 2)]),
    ('frozendict', 'keys', 'display'): (['5', 'H1', 'H2'], [('hash', 1), ('hash', 2)]),
    ('frozendict', 'keys', 'union'): (['5', 'H1', 'H2'], [('hash', 1), ('hash', 2), ('hash', 1), ('hash', 2)]),
    ('frozendict', 'values', 'set'): (['H3', 'H4'], [('hash', 3), ('hash', 4), ('hash', 5), ('eq', 3, 5)]),
    ('frozendict', 'values', 'frozenset'): (['H3', 'H4'], [('hash', 3), ('hash', 4), ('hash', 5), ('eq', 3, 5)]),
    ('frozendict', 'values', 'update'): (['H3', 'H4'], [('hash', 3), ('hash', 4), ('hash', 5), ('eq', 3, 5)]),
    ('frozendict', 'values', 'display'): (['H3', 'H4'], [('hash', 3), ('hash', 4), ('hash', 5), ('eq', 3, 5)]),
    ('frozendict', 'values', 'union'): (['5', 'H1', 'H2'], [('hash', 1), ('hash', 2), ('hash', 3), ('eq', 1, 3), ('hash', 4), ('eq', 2, 4), ('hash', 5), ('eq', 1, 5)]),
    ('frozendict', 'items', 'set'): (['(5, H5)', '(H1, H3)', '(H2, H4)'], [('hash', 1), ('hash', 3), ('hash', 2), ('hash', 4), ('hash', 5)]),
    ('frozendict', 'items', 'frozenset'): (['(5, H5)', '(H1, H3)', '(H2, H4)'], [('hash', 1), ('hash', 3), ('hash', 2), ('hash', 4), ('hash', 5)]),
    ('frozendict', 'items', 'update'): (['(5, H5)', '(H1, H3)', '(H2, H4)'], [('hash', 1), ('hash', 3), ('hash', 2), ('hash', 4), ('hash', 5)]),
    ('frozendict', 'items', 'display'): (['(5, H5)', '(H1, H3)', '(H2, H4)'], [('hash', 1), ('hash', 3), ('hash', 2), ('hash', 4), ('hash', 5)]),
    ('frozendict', 'items', 'union'): (['(5, H5)', '(H1, H3)', '(H2, H4)', '5', 'H1', 'H2'], [('hash', 1), ('hash', 2), ('hash', 1), ('hash', 3), ('hash', 2), ('hash', 4), ('hash', 5)]),
    ('frozendict', 'bad', 'values'): (('KeyError', "'hash'"), [('hash', 9)]),
    ('frozendict', 'bad', 'items'): (('KeyError', "'hash'"), [('hash', 9)]),
    ('dict', 'same', 'keys'): (['H1'], [('hash', 1)]),
}
assert_eq(len(CASES), 35)
for key, expected in CASES.items():
    assert_eq(run(CALLS[key]), expected, repr(key))
def g():
    yield set(same.items())
assert_eq(run(lambda: next(g())), (['(H1, 0)'], [('hash', 1)]))
