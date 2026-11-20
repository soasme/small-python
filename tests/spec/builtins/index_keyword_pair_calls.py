# spec: PLS-315 23.1.5, 24.1.3
# description: split's and rsplit's sep with maxsplit, and hex's sep with
# bytes_per_sep, both given by keyword in either order, plainly or by
# **, with an object whose Python __index__ may loop, convert as the
# positional call's do: the __index__ before sep's check, its exception
# or a non-int result raising; an unknown or repeated keyword raises
# before it; on str, bytes, bytearray and memoryview, bound and unbound,
# inside functions as at module level.
from harness import assert_eq

log = []
class X:
    def __init__(self, v): self.v = v
    def __index__(self):
        for _ in (): pass
        log.append(self.v)
        if self.v == "raise": raise LookupError("x")
        return self.v
def t(f):
    try: r = f()
    except Exception as e: r = type(e).__name__ + ": " + str(e)
    out = (r, log[:]); del log[:]; return out
s = "a b  c"
cases = [lambda: s.split(sep=" ", maxsplit=X(1)), lambda: s.split(maxsplit=X(1), sep=" "), lambda: s.rsplit(sep=None, maxsplit=X(1)),
         lambda: s.split(**{"sep": " ", "maxsplit": X(1)}), lambda: s.split(**{"maxsplit": X(1), "sep": " "}),
         lambda: str.split(s, sep=" ", maxsplit=X(1)), lambda: s.split(sep=1, maxsplit=X(1)), lambda: s.split(sep=" ", maxsplit=X("raise")),
         lambda: s.split(sepp=" ", maxsplit=X(1)), lambda: s.split(" ", sep=" ", maxsplit=X(1)), lambda: s.split(sep=" ", maxsplit=X("s")),
         lambda: b"a b".split(sep=b" ", maxsplit=X(0)), lambda: bytearray(b"a b").split(sep=b" ", maxsplit=X(0)),
         lambda: b"ab".hex(sep=":", bytes_per_sep=X(1)), lambda: b"ab".hex(bytes_per_sep=X(1), sep=":"), lambda: b"ab".hex(sep=1, bytes_per_sep=X(1)),
         lambda: bytearray(b"ab").hex(sep=":", bytes_per_sep=X(1)), lambda: memoryview(b"ab").hex(sep=":", bytes_per_sep=X(1)),
         lambda: b"ab".hex(**{"sep": "::", "bytes_per_sep": X(1)}), lambda: bytes.hex(b"ab", sep=":", bytes_per_sep=X(1)),
         lambda: s.split(sep=" ", maxsplit=1)]
EXPECTED = [
    (['a', 'b  c'], [1]),
    (['a', 'b  c'], [1]),
    (['a b', 'c'], [1]),
    (['a', 'b  c'], [1]),
    (['a', 'b  c'], [1]),
    (['a', 'b  c'], [1]),
    ('TypeError: must be str or None, not int', [1]),
    ('LookupError: x', ['raise']),
    ("TypeError: split() got an unexpected keyword argument 'sepp'. Did you mean 'sep'?", []),
    ('TypeError: split() takes at most 2 arguments (3 given)', []),
    ('TypeError: X.__index__() must return an int, not str', ['s']),
    ([b'a b'], [0]),
    ([bytearray(b'a b')], [0]),
    ('61:62', [1]),
    ('61:62', [1]),
    ("TypeError: object of type 'int' has no len()", [1]),
    ('61:62', [1]),
    ('61:62', [1]),
    ('ValueError: sep must be length 1.', [1]),
    ('61:62', [1]),
    (['a', 'b  c'], []),
]
assert_eq(len(cases), len(EXPECTED))
for i, (f, expected) in enumerate(zip(cases, EXPECTED)):
    assert_eq(t(f), expected, str(i))
def inside(): return [t(f) for f in cases]
assert_eq(inside(), EXPECTED)
