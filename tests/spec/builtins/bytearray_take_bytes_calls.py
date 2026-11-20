# spec: PLS-315 24.2
# description: a bytearray's resize() and take_bytes() convert their one
# positional argument by ToIndex first, so a Python __index__ that
# resizes the array runs once before it is read; take_bytes takes the
# first n bytes, all of them for None, all but the last -n for a negative
# n; their argument, keyword, type, range and size errors; inside
# comprehensions and generators too.
from harness import assert_eq
log = []
class I:
    def __init__(self, a, n, rep=b'xy'): self.a, self.n, self.rep = a, n, rep
    def __index__(self):
        for _ in (): pass
        log.append(self.n); self.a.clear(); self.a.extend(self.rep); return self.n
class NoIndex: pass
class Raise:
    def __index__(self): raise KeyError('i')
class Sub(int): pass
def run(f):
    del log[:]
    a = bytearray(b'abcdef')
    try: r = f(a)
    except Exception as e: r = (type(e).__name__, str(e))
    return r, bytes(a), log[:]
cases = [lambda a: a.take_bytes(I(a, 1)), lambda a: a.resize(I(a, 5)), lambda a: a.take_bytes(I(a, 9)), lambda a: a.resize(I(a, -1)),
         lambda a: a.take_bytes(NoIndex()), lambda a: a.resize(NoIndex()), lambda a: a.take_bytes(Raise()), lambda a: a.take_bytes(Sub(2)),
         lambda a: bytearray.take_bytes(a, I(a, 1)), lambda a: bytearray.resize(a, I(a, 3)), lambda a: a.take_bytes(n=I(a, 1)),
         lambda a: [a.take_bytes(I(a, 1)) for _ in (0,)], lambda a: a.take_bytes(None), lambda a: a.resize(2.5)]
cases += [lambda a: a.resize(size=1), lambda a: a.take_bytes(3.5), lambda a: a.take_bytes('x'), lambda a: a.resize(-5), lambda a: a.resize(),
          lambda a: a.take_bytes(1, 2), lambda a: a.resize(10**30), lambda a: a.take_bytes(10**30), lambda a: a.take_bytes(-12),
          lambda a: a.take_bytes(-2), lambda a: a.take_bytes(True), lambda a: (a.resize(8), a)[1]]
EXPECTED = [
    (b'x', b'y', [1]),
    (None, b'xy\x00\x00\x00', [5]),
    (('IndexError', "can't take 9 bytes outside size 2"), b'xy', [9]),
    (('ValueError', 'Can only resize to positive sizes, got -1'), b'xy', [-1]),
    (('TypeError', 'n must be an integer or None'), b'abcdef', []),
    (('TypeError', "'NoIndex' object cannot be interpreted as an integer"), b'abcdef', []),
    (('KeyError', "'i'"), b'abcdef', []),
    (b'ab', b'cdef', []),
    (b'x', b'y', [1]),
    (None, b'xy\x00', [3]),
    (('TypeError', 'bytearray.take_bytes() takes no keyword arguments'), b'abcdef', []),
    ([b'x'], b'y', [1]),
    (b'abcdef', b'', []),
    (('TypeError', "'float' object cannot be interpreted as an integer"), b'abcdef', []),
    (('TypeError', 'bytearray.resize() takes no keyword arguments'), b'abcdef', []),
    (('TypeError', 'n must be an integer or None'), b'abcdef', []),
    (('TypeError', 'n must be an integer or None'), b'abcdef', []),
    (('ValueError', 'Can only resize to positive sizes, got -5'), b'abcdef', []),
    (('TypeError', 'bytearray.resize() takes exactly one argument (0 given)'), b'abcdef', []),
    (('TypeError', 'take_bytes expected at most 1 argument, got 2'), b'abcdef', []),
    (('OverflowError', 'Python int too large to convert to C ssize_t'), b'abcdef', []),
    (('IndexError', "cannot fit 'int' into an index-sized integer"), b'abcdef', []),
    (('IndexError', "can't take -6 bytes outside size 6"), b'abcdef', []),
    (b'abcd', b'ef', []),
    (b'a', b'bcdef', []),
    (bytearray(b'abcdef\x00\x00'), b'abcdef\x00\x00', []),
]
assert_eq(len(cases), len(EXPECTED))
for i, (f, expected) in enumerate(zip(cases, EXPECTED)):
    assert_eq(run(f), expected, str(i))
def g(): yield run(cases[0])
assert_eq(list(g()), [EXPECTED[0]])
