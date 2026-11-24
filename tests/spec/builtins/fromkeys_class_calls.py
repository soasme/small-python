# spec: PLS-315 26.1.1, 7.8.2, 26.1.3
# description: dict.fromkeys of a subclass calls the class with no
# arguments, its Python __new__ and __init__ included, then sets each
# element of the iterable, a list, a generator or a map, by the instance's
# Python __setitem__, each before the next element is taken; a frozendict
# subclass is called with a frozendict of the keys. Keys of a dict or set
# keep their hashes, and one with a Python __eq__ compares an earlier one.
# Each of these Python calls may loop, and errors from any of them propagate.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class D(dict):
    def __init__(self, *args):
        spin(); log.append(("init", args)); super().__init__(*args)
    def __setitem__(self, key, value):
        spin(); log.append(("set", key, value)); super().__setitem__(key, value)
class Fresh(dict):
    def __new__(cls):
        spin(); log.append("new"); return {"x": 1}
class Refusing(dict):
    def __setitem__(self, key, value):
        spin()
        if key == 2: raise KeyError("refused")
        super().__setitem__(key, value)
class Failing(dict):
    def __init__(self): spin(); raise ValueError("init")
class F(frozendict):
    def __new__(cls, *args):
        spin(); log.append(("new", len(args))); return super().__new__(cls, *args)
class X(int):
    def __hash__(self):
        log.append(("hash", int(self))); return 13
    def __eq__(self, other):
        spin(); log.append((int(self), int(other))); return False
def gen(*items):
    for item in items:
        spin(); log.append(("yield", item))
        yield item

def check(expression, value, calls, kind=None):
    log.clear()
    result = expression()
    if kind: assert_eq(type(result), kind)
    assert_eq([(int(k) if isinstance(k, X) else k, v) for k, v in result.items()], value)
    assert_eq(log, calls)

def main():
    check(lambda: D.fromkeys([1, 2], 3), [(1, 3), (2, 3)], [("init", ()), ("set", 1, 3), ("set", 2, 3)], D)
    check(lambda: D.fromkeys(gen(7, 8)), [(7, None), (8, None)],
          [("init", ()), ("yield", 7), ("set", 7, None), ("yield", 8), ("set", 8, None)], D)
    check(lambda: D.fromkeys({5: 0}), [(5, None)], [("init", ()), ("set", 5, None)], D)
    check(lambda: D.fromkeys(map(str, [1, 2]), 0), [("1", 0), ("2", 0)], [("init", ()), ("set", "1", 0), ("set", "2", 0)], D)
    check(lambda: Fresh.fromkeys([1]), [("x", 1), (1, None)], ["new"], dict)
    check(lambda: F.fromkeys(gen(1, 2)), [(1, None), (2, None)], [("new", 0), ("yield", 1), ("yield", 2), ("new", 1)], F)
    check(lambda: frozendict.fromkeys(gen(4), 0), [(4, 0)], [("yield", 4)], frozendict)
    check(lambda: dict.fromkeys(gen(6)), [(6, None)], [("yield", 6)], dict)
    # A dict's keys keep their hashes; the second compares the first.
    keyed = {X(1): 1, X(2): 2}
    check(lambda: dict.fromkeys(keyed), [(1, None), (2, None)], [(1, 2)])
    check(lambda: dict.fromkeys(keyed.keys()), [(1, None), (2, None)], [("hash", 1), ("hash", 2), (1, 2)])
    single = set(); single.add(X(5))
    check(lambda: dict.fromkeys(single, 0), [(5, 0)], [])
main()

log.clear()
assert_raises(KeyError, lambda: Refusing.fromkeys([1, 2, 3]))
assert_raises(ValueError, lambda: Failing.fromkeys([1]), message="init")
def broken():
    yield 1
    raise ValueError("gen")
assert_raises(ValueError, lambda: D.fromkeys(broken()), message="gen")
assert_raises(TypeError, lambda: D.fromkeys(5), message="'int' object is not iterable")
