# spec: PLS-315 27.1.1, 27.1.7
# description: the __length_hint__ of an iterator or reversed object over
# an instance calls its Python __len__, which may loop, raise, or return
# what is no usable length, for each hint; a reversed object with no items
# left, or of an empty sequence, gives 0 without calling it.
from harness import *

log = []
class S:
    def __init__(s, n): s.n = n
    def __len__(s):
        for _ in (): pass
        log.append("len")
        if isinstance(s.n, BaseException): raise s.n
        return s.n
    def __getitem__(s, i):
        if i >= 3: raise IndexError
        return i
class I:
    def __init__(s, v): s.v = v
    def __index__(s): return s.v
def t(f):
    del log[:]
    try: return (f(), log[:])
    except Exception as e: return (type(e).__name__, str(e), log[:])

def hints():
    out = []
    for n in (3, 0, -1, 2**70, "x", True, ZeroDivisionError("z")):
        out.append((t(lambda: iter(S(n)).__length_hint__()),
                    t(lambda: reversed(S(n) if not isinstance(n, int) or n >= 0 else S(3)).__length_hint__())))
    it = iter(S(3)); next(it); out.append(t(lambda: it.__length_hint__()))
    r = reversed(S(3)); next(r); out.append((t(lambda: r.__length_hint__()), t(lambda: type(r).__length_hint__(r))))
    next(r); next(r); out.append(t(lambda: r.__length_hint__()))
    it = iter(S(3)); list(it); out.append(t(lambda: it.__length_hint__()))
    class N:
        def __getitem__(s, i): raise IndexError
    out.append(t(lambda: iter(N()).__length_hint__()))
    return out

over = "cannot fit 'int' into an index-sized integer"
expected = [((3, ["len"]), (3, ["len", "len"])), ((0, ["len"]), (0, ["len"])),
            (("ValueError", "__len__() should return >= 0", ["len"]), (3, ["len", "len"])),
            (("OverflowError", over, ["len"]), ("OverflowError", over, ["len"])),
            (("TypeError", "'str' object cannot be interpreted as an integer", ["len"]),
             ("TypeError", "'str' object cannot be interpreted as an integer", ["len"])),
            ((1, ["len"]), (1, ["len", "len"])), (("ZeroDivisionError", "z", ["len"]), ("ZeroDivisionError", "z", ["len"])),
            (2, ["len"]), ((2, ["len"]), (2, ["len"])), (0, []), (0, []), (NotImplemented, [])]
assert_eq(hints(), expected)
assert_eq(iter(S(4)).__length_hint__(), 4)

# A native __len__ gives the hint as well, also of an iterable instance
# that list() and bytes() consume.
class NativeSized:
    __len__ = [1, 2, 3].__len__
    def __getitem__(self, i):
        if i >= 3: raise IndexError
        return i
class NativeSizedIterable:
    __len__ = [1].__len__
    def __iter__(self): return iter([5, 6])
assert_eq([list(iter(NativeSized())), list(reversed(NativeSized())), list(NativeSizedIterable()), bytes(NativeSizedIterable())],
          [[0, 1, 2], [2, 1, 0], [5, 6], b"\x05\x06"])
native_it, native_back = iter(NativeSized()), reversed(NativeSized())
native_hints = [native_it.__length_hint__(), native_back.__length_hint__()]
next(native_it); next(native_back)
native_hints += [native_it.__length_hint__(), native_back.__length_hint__()]
assert_eq(native_hints, [3, 3, 2, 2])
# A native __len__ bound elsewhere is called for the hint; a hint that is
# not an int is ignored.
class HintNative:
    __len__ = [1, 2, 3].__len__
    def __iter__(self): return iter([4, 5])
class Seq:
    __len__ = [1, 2, 3].__len__
    def __getitem__(self, i):
        if i > 1: raise IndexError
        return i
class HintBad:
    __len__ = "x".upper
    def __getitem__(self, i):
        if i > 1: raise IndexError
        return i
def native_hints():
    out = [list(HintNative()), list(iter(Seq())), bytes(HintNative()), bytearray(iter(Seq())), [9] + list(iter(Seq()))]
    l = []; l.extend(HintNative()); out.append(l)
    for f in (lambda: list(iter(HintBad())), lambda: list(HintBad())):
        try: out.append(f())
        except TypeError as e: out.append(str(e))
    return out
assert_eq(native_hints(), [[4, 5], [0, 1], b"\x04\x05", bytearray(b"\x00\x01"), [9, 0, 1], [4, 5], [0, 1], [0, 1]])
