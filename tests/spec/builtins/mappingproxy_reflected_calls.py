# spec: PLS-315 26.6, 7.2.4
# description: x == proxy and x != proxy, x a builtin value declining the
# comparison, are the mappingproxy's reflected comparison: its mapping
# compared with x, the mapping's Python __eq__ or __ne__ first, then x's
# reflected one, each of which may loop; an exact dict mapping reaches x
# as a copy. In a plain expression, a chain and a test, inside functions
# and generators as at module level.
from harness import *

Proxy = type(type.__dict__)
log = []

class M:
    def __init__(self, d): self.d = d
    def __getitem__(self, k): return self.d[k]
    def keys(self): return self.d.keys()
    def __eq__(self, other):
        for _ in range(2): pass
        log.append(("eq", type(other).__name__))
        return NotImplemented if other == [] else self.d == other
    def __ne__(self, other):
        for _ in range(2): pass
        log.append(("ne", type(other).__name__))
        return self.d != other

def run(f):
    del log[:]
    return f(), log[:]

def cases():
    p, q = Proxy(M({"a": 1})), Proxy({"a": 1})
    def test():
        if {"a": 1} == p: return "yes"
        return "no"
    return [run(lambda: {"a": 1} == p), run(lambda: {"a": 2} != p), run(lambda: [] == p), run(lambda: 1 == p),
            run(lambda: {"a": 1} == p == {"a": 1}), run(lambda: 0 < 1 == p), run(test),
            run(lambda: {"a": 1} == q), run(lambda: [] != q)]

expected = [(True, [("eq", "dict")]), (True, [("ne", "dict")]), (False, [("eq", "list")]), (False, [("eq", "int")]),
            (True, [("eq", "dict"), ("eq", "dict")]), (False, [("eq", "int")]), ("yes", [("eq", "dict")]),
            (True, []), (True, [])]

def gen():
    yield cases()

assert_eq(cases(), expected)
assert_eq(next(gen()), expected)
def main(): return cases()
assert_eq(main(), expected)
