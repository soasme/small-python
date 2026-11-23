# spec: PLS-315 23.1.5, 23.1.6, 22.1.1, 22.1.5, 24.1.3
# description: A maxsplit, tabsize or int() base given by keyword, and
# bytes.hex's bytes_per_sep and int.to_bytes' length, given an object
# with a Python __index__ that may loop, convert by it before the
# method's other arguments are checked: hex's separator after its
# group, to_bytes' byte order after its length. Its exception
# propagates and a non-int result raises TypeError. Inside functions as
# at module level.
from harness import *

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
    s = "a b  c"
    return [t(lambda: s.split(maxsplit=X(1))), t(lambda: s.rsplit(" ", maxsplit=X(1))), t(lambda: s.split(sep=" ", maxsplit=X(1))),
            t(lambda: str.split(s, maxsplit=X(1))), t(lambda: b"a b".split(maxsplit=X(0))), t(lambda: [bytes(p) for p in bytearray(b"a b").rsplit(maxsplit=X(0))]),
            t(lambda: "a\tb".expandtabs(tabsize=X(3))), t(lambda: int("11", base=X(2))), t(lambda: int(base=X(2))), t(lambda: int(5, base=X(2))),
            t(lambda: s.split(1, maxsplit=X(1))), t(lambda: s.split(maxsplit=X("raise"))), t(lambda: s.split(maxsplit=X("s"))),
            t(lambda: s.split(None, 1, maxsplit=X(1))), t(lambda: s.split(maxsplit=1.5)), t(lambda: s.split(maxsplitt=X(1))),
            t(lambda: b"ab".hex("::", X(1))), t(lambda: b"ab".hex(1, X(1))), t(lambda: b"ab".hex(":", X(1))), t(lambda: (5).to_bytes(X(1), "bad")), t(lambda: (5).to_bytes(X(1))), t(lambda: bytearray(b"ab").hex(":", X(1))), t(lambda: b"ab".hex(sep=":", bytes_per_sep=X(1)))]

expected = [(['a', 'b  c'], [1]), (['a b ', 'c'], [1]), (['a', 'b  c'], [1]), (['a', 'b  c'], [1]), ([b'a b'], [0]),
            ([b'a b'], [0]), ('a  b', [3]), (3, [2]), ('TypeError: int() missing string argument', []),
            ("TypeError: int() can't convert non-string with explicit base", [2]),
            ('TypeError: must be str or None, not int', [1]), ('LookupError: x', ['raise']),
            ('TypeError: X.__index__() must return an int, not str', ['s']),
            ('TypeError: split() takes at most 2 arguments (3 given)', []),
            ("TypeError: 'float' object cannot be interpreted as an integer", []),
            ("TypeError: split() got an unexpected keyword argument 'maxsplitt'. Did you mean 'maxsplit'?", []),
            ('ValueError: sep must be length 1.', [1]), ("TypeError: object of type 'int' has no len()", [1]),
            ('61:62', [1]), ("ValueError: byteorder must be either 'little' or 'big'", [1]), (b'\x05', [1]),
            ('61:62', [1]), ('61:62', [1])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)

# A keyword unpacked from a dict, or given with starred positional
# arguments, converts the same way.
class UnpackedIndex:
    def __index__(self): return 1
unpacked_args = ("a b c",)
assert_eq([str.split(*unpacked_args, maxsplit=UnpackedIndex()), "a b c".split(**{"maxsplit": UnpackedIndex()}),
           "a b c".split(" ", **{"maxsplit": UnpackedIndex()})], [["a", "b c"]] * 3)
assert_eq([int.to_bytes(*(5,), length=UnpackedIndex()), (5).to_bytes(**{"length": UnpackedIndex()})], [b"\x05"] * 2)
