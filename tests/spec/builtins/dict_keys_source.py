# spec: PLS-315 26.1.1
# description: dict() and dict.update() of an object with a keys
# attribute merge it as a mapping, by keys() and __getitem__, even when
# its class also has an __iter__ on the machine, or the attribute is the
# instance's own or a __getattr__'s, which is asked for it again to
# merge; one without keys takes the pairs its __iter__ gives, and an
# error other than AttributeError from the lookup propagates, inside
# functions as at module level.
from harness import *

class Both:
    def __iter__(self): return iter([("x", 1)])
    def keys(self): return ["a", "b"]
    def __getitem__(self, k): return k * 2

class Pairs:
    def __iter__(self):
        yield ("p", 1)
        yield ("q", 2)

class Own:
    def __init__(self): self.keys = lambda: ["k"]
    def __iter__(self): return iter([("x", 1)])
    def __getitem__(self, k): return k + "!"

log = []

class Dynamic:
    def __getattr__(self, name):
        log.append(name)
        if name == "keys": return lambda: ["d"]
        raise AttributeError(name)
    def __iter__(self): return iter([("x", 1)])
    def __getitem__(self, k): return k * 3

class Broken:
    def __getattr__(self, name): raise KeyError(name)
    def __iter__(self): return iter([("x", 1)])

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    d = {}
    d.update(Both())
    return [dict(Both()), d, dict(Pairs()), dict(Own()), {**Both()}, dict(Dynamic()), error(lambda: dict(Broken())), list(log)]

expected = [{'a': 'aa', 'b': 'bb'}, {'a': 'aa', 'b': 'bb'}, {'p': 1, 'q': 2}, {'k': 'k!'}, {'a': 'aa', 'b': 'bb'},
            {'d': 'ddd'}, ('KeyError', "'keys'"), ['keys', 'keys']]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
