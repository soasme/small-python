# spec: PLS-315 23.1.4, 24.3, 25.5.2
# description: a str's or bytes' find, rfind, index, rindex, count,
# startswith and endswith, and a list's or tuple's index(), call a bound's
# Python __index__ in turn, start then end, and search with the ints it
# returns; a bound may be None for a str or bytes. A str's find-like
# methods refuse a needle other than str first; startswith and the bytes
# methods convert the bounds before examining their argument. A non-int
# result raises before the later bound, and an arity error before any.
# Also through a bound method value and starred arguments; inside
# functions as at module level.
from harness import *

log = []

class I:
    def __init__(self, v): self.v = v
    def __index__(self):
        for _ in (): pass
        log.append(self.v)
        return self.v

class Bad:
    def __index__(self):
        for _ in (): pass
        log.append("bad")
        return "x"

def run():
    out = []
    for name in ("find", "rfind", "index", "rindex", "count", "startswith", "endswith"):
        out.append(getattr("abcabc", name)("b", I(1), I(5)))
        out.append(getattr(b"abcabc", name)(b"b", None, I(-1)))
    out.append("abcabc".find("c", I(3)))
    bound = "abcabc".count
    out.append(bound(*("a", I(0), I(4))))
    out.append([1, 2, 1, 2].index(1, I(1)))
    out.append((1, 2, 1, 2).index(2, I(2), I(4)))
    for call in (lambda: "abc".find(1, I(7)), lambda: "abc".startswith(1, I(8)), lambda: b"abc".count("x", I(9)),
                 lambda: "abc".find("a", Bad(), I(10)), lambda: [1].index(1, None, I(11)), lambda: "abc".find(),
                 lambda: b"abc".startswith()):
        try: call()
        except TypeError as e: out.append(str(e))
    return out

expected = [1, 1, 4, 4, 1, 1, 4, 4, 2, 2, True, False, True, True, 5, 2, 2, 3,
            "find() argument 1 must be str, not int", "startswith first arg must be str or a tuple of str, not int",
            "argument should be integer or bytes-like object, not 'str'",
            "Bad.__index__() must return an int, not str", "slice indices must be integers or have an __index__ method",
            "find expected at least 1 argument, got 0", "startswith expected at least 1 argument, got 0"]
expected_log = [1, 5, -1] * 7 + [3, 0, 4, 1, 2, 4, 8, 9, "bad"]
assert_eq(run(), expected)
assert_eq(log, expected_log)
log.clear()
assert_eq("abcabc".rfind("a", I(0), None), 3)
assert_eq(log, [0])
