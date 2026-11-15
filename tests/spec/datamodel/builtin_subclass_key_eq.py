# spec: PLS-315 7.5.7, 26.2, 26.3
# description: a dict or set lookup whose key, or a stored key, is an
# instance of a builtin type's subclass with a Python __eq__ compares
# entries of an equal hash with it as it does any instance's: a
# subscript, in, a store, a deletion, get, a set method of a list, and a
# display, each comparison once, in order; a raising __eq__ propagates;
# a plain key compares with a stored one by its Python __eq__ too.
# Inside functions as at module level.
from harness import *

log = []

class S(str):
    def __eq__(self, o):
        for _ in (): pass
        log.append(("S", str(self), o))
        return str(self) == o
    __hash__ = str.__hash__

class I(int):
    def __eq__(self, o):
        for _ in (): pass
        log.append(("I", int(self), int(o)))
        return int(self) == o
    __hash__ = int.__hash__

class Bad(int):
    def __eq__(self, o): raise LookupError(int(self))
    __hash__ = int.__hash__

def run():
    out = []
    d = {"a": 1, I(2): 2}
    out.append((d[S("a")], S("a") in d, S("z") in d, d.get(S("a")), d[2], 2 in d))
    d[S("a")] = 5
    del d[S("a")]
    out.append(sorted((int(k), v) for k, v in d.items()))
    s = {I(1), I(2)}
    out.append((1 in s, 3 in s, sorted(map(int, s.union([1, 3]))), sorted(map(int, s.intersection([2]))), s.isdisjoint([2]),
                sorted(map(int, {I(4), 4}))))
    try: {I(7): 0}[Bad(7)]
    except LookupError as e: out.append(e.args)
    return out

expected = [(1, True, False, 1, 2, True), [(2, 2)],
            (True, False, [1, 2, 3], [2], False, [4]), (7,)]
expected_log = [("S", "a", "a"), ("S", "a", "a"), ("S", "a", "a"), ("I", 2, 2), ("I", 2, 2),
                ("S", "a", "a"), ("S", "a", "a"), ("I", 1, 1), ("I", 1, 1), ("I", 2, 2), ("I", 2, 2),
                ("I", 4, 4), ("I", 7, 7)]
assert_eq(run(), expected)
assert_eq(log, expected_log)
log.clear()
d = {I(3): "x"}
assert_eq((d[3], 3 in {I(3)}, log), ("x", True, [("I", 3, 3), ("I", 3, 3)]))
