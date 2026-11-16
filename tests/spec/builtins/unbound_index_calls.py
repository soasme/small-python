# spec: PLS-315 23.1.4, 25.1, 25.5.4, 7.5.3
# description: An unbound list.pop, list.insert, list.index, tuple.index
# or str, bytes or bytearray search, given an object with a Python
# __index__, converts it as the bound method does, in order, before the
# method reads the sequence; its exception propagates. An unbound search
# given no object, or one of another type, names its descriptor. Inside
# functions as at module level.
from harness import *

log = []
class X:
    def __init__(self, v): self.v = v
    def __index__(self):
        for _ in range(2): pass
        log.append(self.v)
        if self.v == "raise": raise LookupError("x")
        return self.v
class L(list): pass
def t(f):
    try: r = f()
    except Exception as e: r = type(e).__name__ + ": " + str(e)
    out = (r, log[:]); del log[:]; return out
def results():
    l = [1, 2, 3, 2]
    return [t(lambda: list.pop(l, X(1))), t(lambda: list(l)), t(lambda: list.insert(l, X(0), 9)), t(lambda: list(l)),
            t(lambda: list.index(l, 2, X(2))), t(lambda: tuple.index((1, 2, 1), 1, X(1), X(3))), t(lambda: list.pop(L([5, 6]), X(0))),
            t(lambda: str.find("abcb", "b", X(2))), t(lambda: str.count("abcb", "b", None, X(3))), t(lambda: str.find("abc", 1, X(1))),
            t(lambda: str.startswith("abc", ("b", "c"), X(1))), t(lambda: bytes.find(b"abcb", b"b", X(2))), t(lambda: bytearray.find(bytearray(b"abcb"), 98, X(2))),
            t(lambda: list.pop([], X(0))), t(lambda: list.pop(l, X("raise"))), t(lambda: list.index(l, 2, None)), t(lambda: list.pop((1,), X(0))),
            t(lambda: str.find(1, "a", X(0))), t(lambda: list.index(l, 7, X(0))), t(lambda: list.insert(l, X(1))),
            t(lambda: str.find()), t(lambda: bytes.count(1, b"a")), t(lambda: bytearray.startswith(b"a", b"a")),
            t(lambda: str.endswith(None, "")), t(lambda: direct())]

def direct():
    l = [1, 2, 3]
    a = list.pop(l, X(0)); list.insert(l, X(1), 7); b = str.find("abcb", "b", X(2)); c = tuple.index((1, 2), 2, X(0))
    return a, l, b, c

expected = [(2, [1]), ([1, 3, 2], []), (None, [0]), ([9, 1, 3, 2], []), (3, [2]), (2, [1, 3]), (5, [0]), (3, [2]),
            (1, [3]), ('TypeError: find() argument 1 must be str, not int', []), (True, [1]), (3, [2]), (3, [2]),
            ('IndexError: pop from empty list', [0]), ('LookupError: x', ['raise']),
            ('TypeError: slice indices must be integers or have an __index__ method', []),
            ("TypeError: descriptor 'pop' for 'list' objects doesn't apply to a 'tuple' object", []),
            ("TypeError: descriptor 'find' for 'str' objects doesn't apply to a 'int' object", []),
            ('ValueError: list.index(x): x not in list', [0]), ('TypeError: insert expected 2 arguments, got 1', []),
            ('TypeError: unbound method str.find() needs an argument', []),
            ("TypeError: descriptor 'count' for 'bytes' objects doesn't apply to a 'int' object", []),
            ("TypeError: descriptor 'startswith' for 'bytearray' objects doesn't apply to a 'bytes' object", []),
            ("TypeError: descriptor 'endswith' for 'str' objects doesn't apply to a 'NoneType' object", []),
            ((1, [2, 7, 3], 3, 1), [0, 1, 2, 0])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
