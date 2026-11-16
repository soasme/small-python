# spec: PLS-315 23.1.6, 23.1.5, 22.1.1
# description: A str's, bytes' or bytearray's center, ljust, rjust and
# zfill width, expandtabs tab size and split and rsplit maxsplit, and
# int()'s base, given an object with a Python __index__ that may loop,
# convert by it before the other arguments are checked; its exception
# propagates, a non-int result raises TypeError, a too large width
# OverflowError, and int() checks the base's range before the value's
# type. Inside functions as at module level.
from harness import *

args = (5, None)
log = []
class X:
    def __init__(self, v): self.v = v
    def __index__(self):
        for _ in range(2): pass
        log.append(self.v)
        if self.v == "raise": raise LookupError("x")
        return self.v
def t(f):
    try: r = f()
    except Exception as e: r = type(e).__name__ + ": " + str(e)
    out = (r, log[:]); del log[:]; return out
def results():
    global args
    args = (5, X(2))
    s, b, ba = "a b c", b"a b", bytearray(b"a b")
    return [t(lambda: s.ljust(X(7), "*")), t(lambda: s.rjust(X(6))), t(lambda: s.center(X(9), "-")), t(lambda: s.zfill(X(7))),
            t(lambda: "a\tb".expandtabs(X(4))), t(lambda: s.split(None, X(1))), t(lambda: s.rsplit(" ", X(1))),
            t(lambda: b.ljust(X(5))), t(lambda: b.split(None, X(0))), t(lambda: [bytes(p) for p in ba.split(b" ", X(1))]), t(lambda: bytes(ba.zfill(X(5)))),
            t(lambda: int("11", X(2))), t(lambda: int("z", X(36))), t(lambda: int(5, X(2))), t(lambda: int("1", X(99))),
            t(lambda: s.ljust(X("raise"))), t(lambda: s.ljust(X("s"))), t(lambda: s.ljust(X(3), "ab")), t(lambda: s.ljust(X(3), 1)),
            t(lambda: s.split(1, X(1))), t(lambda: s.zfill(X(3), 1)), t(lambda: s.ljust(X(1 << 70))), t(lambda: str.ljust(s, X(6))),
            t(lambda: [s.center(X(7)), 1]), t(lambda: s.ljust(X(-1))), t(lambda: int("1", X(1 << 70))), t(lambda: s.expandtabs(X(2), 1)), t(lambda: int(*args)), t(lambda: int(5, 99)),
            t(lambda: list(map(int, ['11'], [X(2)])))]

expected = [('a b c**', [7]), (' a b c', [6]), ('--a b c--', [9]), ('00a b c', [7]), ('a   b', [4]),
            (['a', 'b c'], [1]), (['a b', 'c'], [1]), (b'a b  ', [5]), ([b'a b'], [0]), ([b'a', b'b'], [1]),
            (b'00a b', [5]), (3, [2]), (35, [36]),
            ("TypeError: int() can't convert non-string with explicit base", [2]),
            ('ValueError: int() base must be >= 2 and <= 36, or 0', [99]), ('LookupError: x', ['raise']),
            ('TypeError: X.__index__() must return an int, not str', ['s']),
            ('TypeError: The fill character must be exactly one character long', [3]),
            ('TypeError: The fill character must be a unicode character, not int', [3]),
            ('TypeError: must be str or None, not int', [1]),
            ('TypeError: str.zfill() takes exactly one argument (2 given)', []),
            ('OverflowError: Python int too large to convert to C ssize_t', [1180591620717411303424]), ('a b c ', [6]),
            ([' a b c ', 1], [7]), ('a b c', [-1]),
            ('ValueError: int() base must be >= 2 and <= 36, or 0', [1180591620717411303424]),
            ('TypeError: expandtabs() takes at most 1 argument (2 given)', []),
            ("TypeError: int() can't convert non-string with explicit base", [2]),
            ('ValueError: int() base must be >= 2 and <= 36, or 0', []), ([3], [2])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
