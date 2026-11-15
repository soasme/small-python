# spec: PLS-315 13.2.3, 13.3.4
# description: ** of a dict or frozendict subclass that does not override
# __iter__ merges the object's own entries, calling neither its keys nor
# its __getitem__, in a call as in a display, as dict(), dict.update()
# and | do; one that overrides __iter__ merges through keys and
# __getitem__. Inside functions as at module level.
from harness import *

log = []

class D(dict):
    def keys(self):
        log.append("keys")
        return ["a"]
    def __getitem__(self, k):
        log.append("get")
        return 1

class DI(D):
    def __iter__(self): return iter(["z"])

class F(frozendict):
    def keys(self):
        log.append("keys")
        return ["a"]
    def __getitem__(self, k):
        log.append("get")
        return 1

def f(**k): return k

def results():
    del log[:]
    d, di, fr = D({"q": 2}), DI({"q": 2}), F({"q": 2})
    out = [f(**d), {**d}, f(**fr), {**fr}, {"p": 0, **d}, dict(d), {} | d, list(log)]
    out += [f(**di), {**di}, list(log)]
    return out

expected = [{"q": 2}, {"q": 2}, {"q": 2}, {"q": 2}, {"p": 0, "q": 2}, {"q": 2}, {"q": 2}, [],
            {"a": 1}, {"a": 1}, ["keys", "get", "keys", "get"]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
