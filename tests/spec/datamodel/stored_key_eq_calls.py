# spec: PLS-315 26.1, 26.2, 26.3, 13.2.2, 13.2.3
# description: a lookup of a builtin key, an int, str or tuple, in a dict,
# frozendict, set or frozenset that holds a key of the same hash with a
# Python __eq__ compares them by that __eq__, the stored key's: a
# subscript, in and not in, alone and in a test, a store, a deletion, and
# a dict or set display's later key; the stored key stays, its value
# replaced; a raising __eq__ propagates; a key of another hash compares
# with none. Inside functions as at module level.
from harness import *

log = []

class I(int):
    def __eq__(self, o):
        for _ in (): pass
        log.append(("I", int(self), o))
        return int(self) == o
    __hash__ = int.__hash__

class T(str):
    def __eq__(self, o):
        for _ in (): pass
        log.append(("T", str(self), o))
        return str(self) == o
    __hash__ = str.__hash__

class Bad(int):
    def __eq__(self, o): raise LookupError(int(self), o)
    __hash__ = int.__hash__

def run():
    out = []
    d = {"a": 1, I(2): 2, T("b"): 3}
    out.append((d[2], d["b"], 2 in d, 3 in d, "b" not in d))
    if 2 in d and "b" in d: out.append("test")
    d[2] = 20
    out.append([(type(k).__name__, v) for k, v in d.items()])
    del d["b"]
    out.append(sorted(map(str, d)))
    f = frozendict({I(5): 5})
    s, z = {I(1), I(2)}, frozenset({T("c")})
    out.append((f[5], 5 in f, 1 in s, 3 in s, "c" in z))
    out.append([type(k).__name__ for k in {I(4): 1, 4: 2}] + [type(k).__name__ for k in {I(4), 4}])
    out.append({I(6): "x", 6: "y"}[6])
    try: {Bad(7): 0}[7]
    except LookupError as e: out.append(e.args)
    return out

expected = [(2, 3, True, False, False), "test", [("str", 1), ("I", 20), ("T", 3)], ["2", "a"], (5, True, True, False, True),
            ["I", "I"], "y", (7, 7)]
expected_log = [("I", 2, 2), ("T", "b", "b"), ("I", 2, 2), ("T", "b", "b"), ("I", 2, 2), ("T", "b", "b"), ("I", 2, 2),
                ("T", "b", "b"), ("I", 5, 5), ("I", 5, 5), ("I", 1, 1), ("T", "c", "c"), ("I", 4, 4), ("I", 4, 4),
                ("I", 6, 6), ("I", 6, 6)]
assert_eq(run(), expected)
assert_eq(log, expected_log)
log.clear()
d = {I(3): "x"}
assert_eq((d[3], 3 in {I(3)}, (3,) in {(I(3),): 1}, log), ("x", True, True, [("I", 3, 3), ("I", 3, 3), ("I", 3, 3)]))
