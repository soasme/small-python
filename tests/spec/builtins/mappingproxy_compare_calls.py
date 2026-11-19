# spec: PLS-315 26.6, 7.2.4
# description: == and != of a mappingproxy on the left compare its
# mapping with the other operand as a rich comparison of their own: the
# mapping's Python __eq__ or __ne__, or the other's reflected one, each of
# which may loop and pause in a generator, an exact dict reaching the
# other operand, unless a dict or a mappingproxy, only as a copy, and a
# proxy of a proxy comparing the inner mapping. In a plain expression, a
# chain and a test, inside functions as at module level.
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
        return isinstance(other, M) and self.d == other.d
    def __ne__(self, other):
        for _ in range(2): pass
        log.append(("ne", type(other).__name__))
        return not (isinstance(other, M) and self.d == other.d)
class Other:
    def __eq__(self, other):
        for _ in range(2): pass
        log.append(("other", type(other).__name__))
        if type(other) is dict: other["seen"] = 1
        return "other"
class Value:
    def __init__(self, v): self.v = v
    def __eq__(self, other):
        for _ in range(2): pass
        log.append(("value", self.v))
        return isinstance(other, Value) and self.v == other.v
class Ns:
    x = 1

def compare():
    p = Proxy(M({"a": 1}))
    out = [p == M({"a": 1}), p != M({"a": 2}), p == M({"a": 2})]
    if p == M({"a": 1}): out.append("test")
    out.append(1 < 2 and p == M({"a": 1}))
    out.append(0 < 1 == 1 != p)
    namespace = Proxy(Ns.__dict__)
    out.append(namespace == Other())
    out.append("seen" in Ns.__dict__)
    out.append(Proxy(Proxy(M({"b": 2}))) == M({"b": 2}))
    out.append(Proxy({"k": Value(1)}) == {"k": Value(1)})
    out.append(Proxy({"k": Value(1)}) != {"k": Value(2)})
    try:
        p < M({})
    except TypeError as e:
        out.append(str(e))
    return out, log[:]

expected = ([True, True, False, "test", True, True, "other", False, True, True, True,
             "'<' not supported between instances of 'mappingproxy' and 'M'"],
            [("eq", "M"), ("ne", "M"), ("eq", "M"), ("eq", "M"), ("eq", "M"), ("ne", "int"),
             ("other", "dict"), ("eq", "M"), ("value", 1), ("value", 1)])

def paused():
    def gen():
        p = Proxy(M({"a": 1}))
        yield p == M({"a": 1})
        yield p != M({"a": 1})
    return list(gen()), log[:]

def results():
    del log[:]
    out = compare()
    del log[:]
    return out, paused()

expected_all = (expected, ([True, False], [("eq", "M"), ("ne", "M")]))

def main():
    return results()

assert_eq(main(), expected_all)
assert_eq(results(), expected_all)
