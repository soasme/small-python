# spec: PLS-315 24.2
# description: storing a byte at an int index of a bytearray, or of its
# subclass's instance, converts the value by its Python __index__ once,
# before the index is checked against the length, which that call may
# change; its result must be an int in range(0, 256); a key of another
# type fails first; inside comprehensions and generators too.
from harness import assert_eq
log = []
class V:
    def __init__(self, a, v, rep=None): self.a, self.v, self.rep = a, v, rep
    def __index__(self):
        for _ in (): pass
        log.append(self.v)
        if self.rep is not None: self.a[:] = self.rep
        return self.v
class Bad:
    def __index__(self): return 'x'
class Raise:
    def __index__(self): raise KeyError('v')
class BA(bytearray): pass
def run(f):
    del log[:]
    a = bytearray(b'abc')
    try: f(a); r = 'ok'
    except Exception as e: r = (type(e).__name__, str(e))
    return r, bytes(a), log[:]
def s0(a): a[0] = V(a, 65)
def s1(a): a[-1] = V(a, 66)
def s2(a): a[2] = V(a, 67, b'')
def s3(a): a[0] = V(a, 300)
def s4(a): a[0] = Bad()
def s5(a): a[0] = Raise()
def s6(a): a[5] = V(a, 1)
def s7(a): a[True] = V(a, 68, b'wxyz')
def s8(a): a['k'] = V(a, 1)
def s9(a):
    b = BA(b'xyz'); b[0] = V(b, 69); a[:] = b
def s10(a):
    m = memoryview(a); a[1] = V(a, 70); m.release()
def s11(a):
    for i in range(3): a[i] = V(a, 71 + i)
def s12(a): a[0] = V(a, -1)
cases = [s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12]
EXPECTED = [
    ('ok', b'Abc', [65]),
    ('ok', b'abB', [66]),
    (('IndexError', 'bytearray index out of range'), b'', [67]),
    (('ValueError', 'byte must be in range(0, 256)'), b'abc', [300]),
    (('TypeError', 'Bad.__index__() must return an int, not str'), b'abc', []),
    (('KeyError', "'v'"), b'abc', []),
    (('IndexError', 'bytearray index out of range'), b'abc', [1]),
    ('ok', b'wDyz', [68]),
    (('TypeError', 'bytearray indices must be integers or slices, not str'), b'abc', []),
    ('ok', b'Eyz', [69]),
    ('ok', b'aFc', [70]),
    ('ok', b'GHI', [71, 72, 73]),
    (('ValueError', 'byte must be in range(0, 256)'), b'abc', [-1]),
]
assert_eq(len(cases), len(EXPECTED))
for i, (f, expected) in enumerate(zip(cases, EXPECTED)):
    assert_eq(run(f), expected, str(i))
def g(): yield run(s0)
assert_eq(list(g()), [EXPECTED[0]])
assert_eq([run(f) for f in cases[:3]], EXPECTED[:3])
