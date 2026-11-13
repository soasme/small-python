# spec: PLS-315 26.1.2, 25.5.3, 7.2.5
# description: a pair of two dicts of one length inside lists, tuples or
# dicts compares its values as dict == does, and a pair of lists or tuples
# inside a dict compares its items as sequence == does, calling Python
# __eq__ methods that may loop, nested to any depth; dicts of different
# lengths or a missing key compare no values, an error propagates, and an
# ordering of lists tests their items' equality so before ordering the
# first unequal pair.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class K:
    def __init__(self, v, tag): self.v, self.tag = v, tag
    def __eq__(self, other):
        spin(); log.append(self.tag + getattr(other, "tag", "?"))
        if self.v == 9: raise KeyError("eq")
        if self.v == 7: outer.clear()
        return isinstance(other, K) and other.v == self.v

def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

outer = {}
def main():
    global outer
    check(lambda: [{1: K(1, "a")}, 2] == [{1: K(1, "b")}, 2], True, ["ab"])
    check(lambda: {1: [K(1, "a"), K(2, "c")]} != {1: [K(1, "b"), K(3, "d")]}, True, ["ab", "cd"])
    check(lambda: ({"x": {"y": (K(1, "a"),)}},) == ({"x": {"y": (K(1, "b"),)}},), True, ["ab"])
    check(lambda: {"x": (1, [K(1, "a")])} == {"x": (1, [K(1, "b")])}, True, ["ab"])
    check(lambda: ([{1: K(1, "a")}] == [{1: K(1, "b"), 2: 0}], [{1: K(1, "a")}] == [{2: K(1, "b")}]), (False, False), [])
    check(lambda: [{1: K(1, "a"), 2: K(1, "c")}, K(1, "e")] == [{1: K(2, "b"), 2: K(1, "d")}, K(1, "f")], False, ["ab"])
    outer = {1: {2: K(7, "m")}, 3: K(1, "p")}
    check(lambda: outer == {1: {2: K(7, "n")}, 3: K(2, "q")}, True, ["mn"])
    check(lambda: [{1: K(1, "a")}] == [{1: K(1, "b")}] == [{1: K(1, "c")}], True, ["ab", "bc"])
    check(lambda: error(lambda: [{1: K(1, "a")}] < [{1: K(2, "b")}]),
          ("TypeError", "'<' not supported between instances of 'dict' and 'dict'"), ["ab"])
    check(lambda: error(lambda: {1: [{2: K(9, "z")}]} == {1: [{2: K(1, "y")}]}), ("KeyError", "'eq'"), ["zy"])
    def gen():
        yield [{1: K(1, "a")}] != [{1: K(1, "b")}]
    check(lambda: list(gen()), [False], ["ab"])
main()
