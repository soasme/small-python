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
