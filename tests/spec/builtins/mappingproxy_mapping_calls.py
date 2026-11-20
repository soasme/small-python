# spec: PLS-315 26.6
# description: A mappingproxy's [], iteration and len are those of its
# mapping: a Python __getitem__, __iter__ (a generator function too),
# __len__ or a dict subclass's __missing__, which may loop, is called once
# each, in a loop, a comprehension, a consumer or len(); its reversed()
# calls the mapping's own __reversed__, an AttributeError without one.
from harness import *

P = type(type.__dict__)
log = []
class M:
    def __getitem__(self, k):
        for _ in (): pass
        log.append(("get", k))
        if k == "bad": raise LookupError(k)
        return k * 2
    def __iter__(self):
        for _ in (): pass
        log.append("iter"); return iter("ab")
    def keys(self): return ["a"]
    def __len__(self): log.append("len"); return 2
class G(M):
    def __iter__(self):
        log.append("giter")
        yield "x"; yield "y"
class Missing(dict):
    def __missing__(self, k):
        for _ in (): pass
        log.append(("missing", k)); return k
results = []
for v in (P(M()), P(G()), P(Missing(a=1))):
    del log[:]
    out = [v["q"], tuple(v), sorted(v), list(v), [x for x in v], sorted({*v})]
    for x in v: out.append(x)
    try: v["bad"]
    except LookupError as e: out.append(("raised", str(e)))
    results.append((out, list(log)))
d = P({"a": 1})
results.append((d["a"], list(d), [x for x in d]))
class R(M):
    def __reversed__(self):
        for _ in (): pass
        log.append("rev"); return iter("zy")
    def __len__(self):
        for _ in (): pass
        log.append("len"); return 7
class Bad(M):
    def __len__(self): return -1
del log[:]
v = P(R())
results.append((len(v), list(reversed(v)), list(log)))
try: len(P(Bad()))
except ValueError as e: results.append(str(e))
try: reversed(P(M()))
except AttributeError as e: results.append(str(e))
results.append((len(P({"a": 1})), list(reversed(P({"a": 1, "b": 2})))))
assert_eq(results, [
    (['qq', ('a', 'b'), ['a', 'b'], ['a', 'b'], ['a', 'b'], ['a', 'b'], 'a', 'b', ('raised', 'bad')],
     [('get', 'q'), 'iter', 'iter', 'len', 'iter', 'len', 'iter', 'iter', 'iter', ('get', 'bad')]),
    (['qq', ('x', 'y'), ['x', 'y'], ['x', 'y'], ['x', 'y'], ['x', 'y'], 'x', 'y', ('raised', 'bad')],
     [('get', 'q'), 'giter', 'len', 'giter', 'len', 'giter', 'giter', 'giter', 'giter', ('get', 'bad')]),
    (['q', ('a',), ['a'], ['a'], ['a'], ['a'], 'a'], [('missing', 'q'), ('missing', 'bad')]),
    (1, ['a'], ['a']),
    (7, ['z', 'y'], ['len', 'rev']),
    '__len__() should return >= 0',
    "'M' object has no attribute '__reversed__'",
    (1, ['b', 'a'])])
