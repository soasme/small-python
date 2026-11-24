# spec: PLS-315 25.5.2, 25.5.1, 7.5.4
# description: a list, tuple, str, bytes or bytearray repeated, either way
# round or in place, by an instance whose class defines no multiplication
# but a Python __index__ calls __index__ once and repeats by its int, an
# in-place list repetition keeping its identity; the instance's own
# __rmul__ comes first; a non-int result raises, and a count, or an item's
# index, outside the index-size range raises naming the instance's type;
# inside functions as at module level.
from harness import *

log = []

class X:
    def __init__(self, i): self.i = i
    def __index__(self):
        for _ in (): pass
        log.append(self.i)
        return self.i

class Reflected(X):
    def __rmul__(self, other):
        for _ in (): pass
        return "rmul"

class Real:
    def __index__(self):
        for _ in (): pass
        return 2.0

class Big:
    def __index__(self):
        for _ in (): pass
        return 1 << 70

def repeats():
    out = [[1] * X(2), X(2) * "ab", (1,) * X(0), b"x" * X(3), bytearray(b"y") * X(2), [0] * Reflected(5)]
    a = b = [7]
    a *= X(3)
    out.append((a, a is b))
    s = "q"
    s *= X(2)
    out.append(s)
    out.append(log[:])
    return out

assert_eq(repeats(), [[1, 1], "abab", (), b"xxx", bytearray(b"yy"), "rmul", ([7, 7, 7], True), "qq", [2, 2, 0, 3, 2, 3, 2]])
log.clear()
assert_eq(([2] * X(2), log), ([2, 2], [2]))

def errors():
    out = []
    for operation in (lambda: [1] * Real(), lambda: [1] * Big(), lambda: Big() * "a"):
        try: operation()
        except (TypeError, OverflowError) as e: out.append((type(e).__name__, str(e)))
    for s in ([1], (1,), "a", b"a", bytearray(b"a"), range(3)):
        try: s[Big()]
        except IndexError as e: out.append(str(e))
    return out

assert_eq(errors(), [
    ("TypeError", "Real.__index__() must return an int, not float"),
    ("OverflowError", "cannot fit 'Big' into an index-sized integer"),
    ("OverflowError", "cannot fit 'Big' into an index-sized integer"),
] + ["cannot fit 'Big' into an index-sized integer"] * 5 + ["range object index out of range"])

# A repeat count's __index__ too large for an index names the object.
class RepeatCount:
    def __index__(self): return 2
class RepeatHuge:
    def __index__(self): return 2 ** 70
assert_eq(["ab" * RepeatCount(), RepeatCount() * [1], (1,) * RepeatCount()], ["abab", [1, 1], (1, 1)])
with assert_raises(OverflowError, message="cannot fit 'RepeatHuge' into an index-sized integer"):
    "ab" * RepeatHuge()
# A native __index__, bound elsewhere, gives the count; past an
# index-sized integer the OverflowError names the object's type.
class NativeTwo:
    __index__ = (2).__index__
class NativeHuge:
    __index__ = (2**70).__index__
def native_repeats():
    t, h = NativeTwo(), NativeHuge()
    out = [[1] * t, t * "ab", (1,) * t, b"x" * t, bytearray(b"y") * t]
    for f in (lambda: [1] * h, lambda: "a" * h):
        try: f()
        except OverflowError as e: out.append(str(e))
    return out
assert_eq(native_repeats(), [[1, 1], "abab", (1, 1), b"xx", bytearray(b"yy")] + ["cannot fit 'NativeHuge' into an index-sized integer"] * 2)
