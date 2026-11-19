# spec: PLS-315 26.1.1 13.2.7 13.3.4
# description: A dict or frozendict subclass whose __iter__ is its own
# merges into a dict display's **, a call's ** and dict.update() by its
# Python keys(), whose result is listed first, and its Python
# __getitem__ for each key, in order; one keeping dict's __iter__ merges
# its entries without calling either. An error of keys() or __getitem__
# propagates, a call's duplicate keyword raising before its lookup.
from harness import *

log = []
class D(dict):
    def keys(self):
        for _ in (): pass
        log.append("keys")
        return iter(["a", "b"])
    def __getitem__(self, k):
        for _ in (): pass
        log.append(("get", k))
        if k == "bad": raise KeyError("bad")
        return k * 2
class Own(D):
    def __iter__(self): return iter(["z"])
class Bad(Own):
    def keys(self): return ["a", "bad"]
class F(frozendict):
    keys = D.keys
    __getitem__ = D.__getitem__
    def __iter__(self): return iter(["z"])

def f(**k): return k
def attempt(g):
    try: return g()
    except Exception as e: return (type(e).__name__, str(e))

def results():
    for _ in (): pass
    del log[:]
    d, o, fr = D({"q": 1}), Own({"q": 1}), F({"q": 1})
    u = {}
    u.update(o)
    out = [{**d}, f(**d), {"p": 0, **o}, f(**o), {**fr}, u, attempt(lambda: {**Bad()}), attempt(lambda: f(a=1, **o))]
    return out, list(log)

expected = ([{"q": 1}, {"q": 1}, {"p": 0, "a": "aa", "b": "bb"}, {"a": "aa", "b": "bb"}, {"a": "aa", "b": "bb"},
             {"a": "aa", "b": "bb"}, ("KeyError", "'bad'"),
             ("TypeError", "__main__.f() got multiple values for keyword argument 'a'")],
            ["keys", ("get", "a"), ("get", "b"), "keys", ("get", "a"), ("get", "b"), "keys", ("get", "a"), ("get", "b"),
             "keys", ("get", "a"), ("get", "b"), ("get", "a"), ("get", "bad"), "keys"])

assert_eq(results(), expected)
assert_eq(results(), expected)
