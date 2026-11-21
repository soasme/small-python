# spec: PLS-315 24.1.1, 24.2
# description: bytes(), bytearray() and bytearray.extend() of an iterable,
# a generator or a list or tuple, convert each item by its Python
# __index__ once, in order, an item's result an int in range(0, 256); a
# list an item's conversion changes is read again at each item; inside
# comprehensions and generators too.
from harness import assert_eq
log = []
class V:
    def __init__(self, v, a=None, rep=None): self.v, self.a, self.rep = v, a, rep
    def __index__(self):
        for _ in (): pass
        log.append(self.v)
        if self.a is not None: self.a[:] = self.rep
        return self.v
class Bad:
    def __index__(self): return 'x'
class Raise:
    def __index__(self): raise KeyError('v')
def gen(*items):
    for x in items: yield x
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
a = bytearray(b'ab')
cases = [lambda: bytes(gen(V(65), 66, V(67))), lambda: bytearray(gen(V(1), V(300))), lambda: bytes(gen(Bad())), lambda: bytes(gen(Raise(), V(3))),
         lambda: (a.extend(gen(V(70), V(71))), a)[1], lambda: (a.extend([V(72)]), a)[1], lambda: bytes([V(73), V(74)]), lambda: bytearray((V(75),)),
         lambda: bytes(gen(V(256))), lambda: bytes([V(-1)]), lambda: [bytes(gen(V(76))) for _ in (0,)],
         lambda: (lambda b: (b.extend([V(77, b, b'xyz')]), b)[1])(bytearray(b'q')), lambda: bytearray.extend(bytearray(), [V(78)])]
class Grow:
    def __init__(self, items, v): self.items, self.v = items, v
    def __index__(self):
        for _ in (): pass
        log.append(('grow', self.v)); self.items.append(70 + self.v); return self.v + 64
class Shrink:
    def __init__(self, items): self.items = items
    def __index__(self):
        log.append('shrink'); self.items.clear(); return 65
def mutating(maker):
    items = [1]
    items[0] = Grow(items, 1)
    items.append(2)
    r = maker(items)
    s = [0]; s.append(Shrink(s)); s.append(9)
    return r, maker(s)
more = [lambda: mutating(bytes), lambda: mutating(bytearray), lambda: mutating(lambda x: (lambda b: (b.extend(x), b)[1])(bytearray())),
        lambda: bytes((V(1), 2, V(3))), lambda: bytes([1, 2]), lambda: bytes([V(300)]), lambda: bytearray([Bad()])]
EXPECTED = [
    (b'ABC', [65, 67]),
    (('ValueError', 'byte must be in range(0, 256)'), [1, 300]),
    (('TypeError', 'Bad.__index__() must return an int, not str'), []),
    (('KeyError', "'v'"), []),
    (bytearray(b'abFG'), [70, 71]),
    (bytearray(b'abFGH'), [72]),
    (b'IJ', [73, 74]),
    (bytearray(b'K'), [75]),
    (('ValueError', 'bytes must be in range(0, 256)'), [256]),
    (('ValueError', 'bytes must be in range(0, 256)'), [-1]),
    ([b'L'], [76]),
    (bytearray(b'xyzM'), [77]),
    (None, [78]),
]
assert_eq(len(cases), len(EXPECTED))
for i, (f, expected) in enumerate(zip(cases, EXPECTED)):
    assert_eq(run(f), expected, str(i))
def g(): yield run(cases[0])
assert_eq(list(g()), [EXPECTED[0]])
assert_eq([run(f) for f in more], [((b'A\x02G', b'\x00A'), [('grow', 1), 'shrink']), ((bytearray(b'A\x02G'), bytearray(b'\x00A')), [('grow', 1), 'shrink']), ((bytearray(b'A\x02G'), bytearray(b'\x00A')), [('grow', 1), 'shrink']), (b'\x01\x02\x03', [1, 3]), (b'\x01\x02', []), (('ValueError', 'bytes must be in range(0, 256)'), [300]), (('TypeError', 'Bad.__index__() must return an int, not str'), [])])

# A call site that has cached bytearray.extend still consumes its source on
# the machine, a forward iterator of a list among the sources.
class W2:
    def __init__(self, v): self.v = v
    def __index__(self):
        for _ in (): pass
        log.append(self.v); return self.v
def gen2(*x):
    for i in x: yield i
def site(b, x):
    b.extend(x)
    return b
class BA(bytearray): pass
site_out = []
for src in ([1], gen2(65, W2(66)), [W2(67), 2], (W2(68),), b'xy', 'bad', 5, [W2(300)], gen2(W2(-1)), iter([W2(69)])):
    for b in (bytearray(b'q'), BA(b'r')):
        del log[:]
        try: site_out.append((site(b, src), log[:]))
        except Exception as e: site_out.append((type(e).__name__, str(e), log[:]))
SITE = [
    (bytearray(b'q\x01'), []),
    (BA(b'r\x01'), []),
    (bytearray(b'qAB'), [66]),
    (BA(b'r'), []),
    (bytearray(b'qC\x02'), [67]),
    (BA(b'rC\x02'), [67]),
    (bytearray(b'qD'), [68]),
    (BA(b'rD'), [68]),
    (bytearray(b'qxy'), []),
    (BA(b'rxy'), []),
    ('TypeError', "expected iterable of integers; got: 'str'", []),
    ('TypeError', "expected iterable of integers; got: 'str'", []),
    ('TypeError', "can't extend bytearray with int", []),
    ('TypeError', "can't extend bytearray with int", []),
    ('ValueError', 'byte must be in range(0, 256)', [300]),
    ('ValueError', 'byte must be in range(0, 256)', [300]),
    ('ValueError', 'byte must be in range(0, 256)', [-1]),
    (BA(b'r'), []),
    (bytearray(b'qE'), [69]),
    (BA(b'r'), []),
]
assert_eq(site_out, SITE)
it = iter([W2(1), W2(70), 3]); next(it)
r = []
for mk in (lambda s: bytes(s), lambda s: bytearray(s), lambda s: site(bytearray(b'z'), s)):
    del log[:]
    r.append((mk(iter([W2(71), 4])), mk(iter((5, W2(72)))), log[:]))
del log[:]
assert_eq((r, bytes(it), log), ([(b'G\x04', b'\x05H', [71, 72]), (bytearray(b'G\x04'), bytearray(b'\x05H'), [71, 72]), (bytearray(b'zG\x04'), bytearray(b'z\x05H'), [71, 72])], b'F\x03', [70]))
ex = iter([W2(73)]); list(ex)
assert_eq(bytes(ex), b'')
