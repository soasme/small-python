# spec: PLS-315 7.7.7, 7.7.6
# description: an iterable whose class names a builtin callable as its
# __length_hint__ has it called with no arguments, being no descriptor:
# int gives the hint 0, a TypeError such as abs()'s means no hint, and
# str's '' raises LengthHint's TypeError; list(), tuple(), bytearray() and
# a starred display consume the items after it.
from harness import assert_eq

class Items:
    __length_hint__ = int
    def __iter__(self):
        for _ in (): pass
        return iter([1, 2])

class NoHint(Items):
    __length_hint__ = abs

class Text(Items):
    __length_hint__ = str

def run():
    out = [list(Items()), tuple(Items()), bytearray(Items()), [*Items()], list(NoHint())]
    try: list(Text())
    except TypeError as e: out.append(str(e))
    return out

assert_eq(run(), [[1, 2], (1, 2), bytearray(b"\x01\x02"), [1, 2], [1, 2],
                  "Text.__length_hint__() must return an int, not str"])
