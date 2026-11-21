# spec: PLS-315 25.5.1, 25.3.2, 7.5.3
# description: a sequence's or range's __getitem__, __setitem__ and
# __delitem__ bound to a value the call makes convert a named index by its
# Python __index__ once; its errors and the bounds checks pass out.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class N:
    def __init__(s, v): s.v = v
    def __index__(s):
        log.append(s.v)
        if isinstance(s.v, BaseException): raise s.v
        return s.v
def t(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))
for v in (5, -1, 99, "x", RuntimeError("no")):
    log.clear()
    emit(t(lambda: range(1, 20).__getitem__(N(v))), t(lambda: [1, 2, 3, 4, 5, 6, 7].__getitem__(N(v))),
          t(lambda: "abcdefg".__getitem__(N(v))), t(lambda: (1, 2, 3, 4, 5, 6).__getitem__(N(v))), log)
n = N(2)
log.clear(); emit(range(10, 20).__getitem__(n), bytearray(b"abc").__getitem__(n), b"xyz".__getitem__(n), log)
log.clear(); l = [0, 1, 2, 3]; [0, 1, 2, 3].__setitem__(n, 9); bytearray(b"abc").__delitem__(n); emit(log)
log.clear(); emit(t(lambda: range(9).index(n)), range(1, 2 ** 70).__getitem__(N(2 ** 65)), log)
EXPECTED = [
    '6 6 f 6 [5, 5, 5, 5]',
    '19 7 g 6 [-1, -1, -1, -1]',
    "('IndexError', 'range object index out of range') ('IndexError', 'list index out of range') ('IndexError', 'string index out of range') ('IndexError', 'tuple index out of range') [99, 99, 99, 99]",
    "('TypeError', 'N.__index__() must return an int, not str') ('TypeError', 'N.__index__() must return an int, not str') ('TypeError', 'N.__index__() must return an int, not str') ('TypeError', 'N.__index__() must return an int, not str') ['x', 'x', 'x', 'x']",
    "('RuntimeError', 'no') ('RuntimeError', 'no') ('RuntimeError', 'no') ('RuntimeError', 'no') [RuntimeError('no'), RuntimeError('no'), RuntimeError('no'), RuntimeError('no')]",
    '12 99 122 [2, 2, 2]',
    '[2, 2]',
    "('ValueError', 'sequence.index(x): x not in sequence') 36893488147419103233 [36893488147419103232]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
