# spec: PLS-315 26.1.3, 26.1.1, 27.1.5
# description: dict.update given its dict, unbound, with or without keywords,
# a dict subclass's update, bound or unbound, and map() of a dict's update,
# a list's extend or a str's join call the source's Python keys,
# __getitem__ and iteration, which may loop, as the bound update does; a
# subclass's update stores by DictSetItem, not its Python __setitem__.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class Mapping:
    def keys(self):
        spin(); log.append("keys"); return iter([1, 2])
    def __getitem__(self, key):
        spin(); log.append(key); return key * 10
class Sub(dict):
    def __setitem__(self, key, value):
        log.append("setitem"); super().__setitem__(key, value)
class Failing:
    def keys(self): spin(); raise LookupError("keys")
def gen(*items):
    for item in items:
        spin(); log.append(("yield", item))
        yield item

def check(expression, result, calls):
    log.clear()
    assert_eq(expression(), result)
    assert_eq(log, calls)

def main():
    d = {}
    check(lambda: dict.update(d, Mapping()), None, ["keys", 1, 2])
    assert_eq(d, {1: 10, 2: 20})
    check(lambda: dict.update(d, Mapping(), z=3), None, ["keys", 1, 2])
    assert_eq(d, {1: 10, 2: 20, "z": 3})
    f = dict.update
    check(lambda: f(d, gen((5, 5))), None, [("yield", (5, 5))])
    assert_eq(d[5], 5)
    s = Sub(a=0)
    check(lambda: s.update(Mapping()), None, ["keys", 1, 2])
    check(lambda: s.update(Mapping(), b=1), None, ["keys", 1, 2])
    check(lambda: dict.update(s, gen((7, 7))), None, [("yield", (7, 7))])
    check(lambda: dict.update(s, Mapping(), c=2), None, ["keys", 1, 2])
    assert_eq(dict(s), {"a": 0, 1: 10, 2: 20, "b": 1, 7: 7, "c": 2})
    assert_eq(type(s), Sub)
    e = {}
    check(lambda: list(map(e.update, [Mapping()])), [None], ["keys", 1, 2])
    check(lambda: list(map(dict.update, [e], [gen((8, 8))])), [None], [("yield", (8, 8))])
    assert_eq(e, {1: 10, 2: 20, 8: 8})
    l = []
    check(lambda: list(map(l.extend, [gen(1, 2), [3]])), [None, None], [("yield", 1), ("yield", 2)])
    assert_eq(l, [1, 2, 3])
    log.clear()
    assert_eq(list(map(" ".join, [gen("a", "b"), ["c"]])), ["a b", "c"])
    assert_eq(log, [("yield", "a"), ("yield", "b")])
    log.clear()
    assert_eq(list(filter(l.extend, [gen(4)])), [])
    assert_eq(log, [("yield", 4)])
main()

assert_raises(LookupError, lambda: dict.update({}, Failing()), message="keys")
assert_raises(LookupError, lambda: Sub().update(Failing()), message="keys")
assert_raises(TypeError, lambda: dict.update({}, 1, 2), message="update expected at most 1 argument, got 2")
assert_raises(TypeError, lambda: dict.update(1, Mapping()), message="descriptor 'update' for 'dict' objects doesn't apply to a 'int' object")
assert_raises(ValueError, lambda: dict.update(Sub(), gen((1,))),
              message="dictionary update sequence element #0 has length 1; 2 is required")
