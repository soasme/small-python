# spec: PLS-315 7.5.4, 24.2, 24.4.2, 25.4.2, 25.5.4
# description: A list's, tuple's, str's, bytes', bytearray's, range's or
# memoryview's __getitem__, __setitem__ or __delitem__ called explicitly,
# bound or given its object, with a slice key converts the slice's parts
# by their Python __index__ as a subscript does: the step, the start, then
# the stop, each result checked, stopping at a part neither None nor an
# int; a list's store then iterates its value, a zero step refused first,
# as in a slice assignment statement;
# a bytearray's store of a value no other bytearray copies the value, a
# number or str refused, and converts the slice again; a view's store
# takes its value's buffer first; and so inside a generator.
from harness import assert_eq

log = []
class I:
    def __init__(self, v): self.v = v
    def __index__(self):
        for _ in (): pass
        log.append(self.v)
        if self.v == 'bad': raise LookupError('bad')
        if self.v == 'str': return 'x'
        return self.v
class LS(list): pass
class BS(bytearray): pass
class Vals:
    def __iter__(self):
        log.append('iter'); return iter([65, 66])
class Items:
    def __init__(self, items, fail=False): self.items = items; self.fail = fail
    def __iter__(self):
        for _ in (): pass
        log.append('iter')
        if self.fail: raise LookupError('it')
        return iter(self.items)
def gen():
    log.append('gen'); yield 7; yield 8
def on(obj, f): f(obj); return obj
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def fresh(): return bytearray(b'abcdef')
def view(): return memoryview(bytearray(b'abcdef'))
cases = [
 lambda: [1, 2, 3].__getitem__(slice(I('bad'), None)),
 lambda: [1, 2, 3].__getitem__(slice(I(1), I('bad'))),
 lambda: [1, 2, 3].__getitem__(slice(I('str'), None)),
 lambda: [1, 2, 3].__getitem__(slice(None, None, I(0))),
 lambda: [1, 2, 3].__getitem__(slice(I(5), None, 0)),
 lambda: [1, 2, 3].__getitem__(slice('a', I(1))),
 lambda: [1, 2, 3].__getitem__(slice(I(1), 'a')),
 lambda: [1, 2, 3].__getitem__(slice(I(2 ** 70), None)),
 lambda: LS([1, 2, 3]).__getitem__(slice(I(1), None)),
 lambda: list.__getitem__(LS([1, 2, 3]), slice(I(1), None)),
 lambda: (lambda b: (b.__setitem__(slice(I(0), I(2)), b), b))(fresh()),
 lambda: (lambda b: (b.__setitem__(slice(I(0), I(2)), b), b))(BS(b'xyz')),
 lambda: (lambda b: (b.__setitem__(slice(I(0), I(2)), 5), b))(fresh()),
 lambda: (lambda b: (b.__setitem__(slice(I(0), I(2)), Vals()), b))(fresh()),
 lambda: (lambda b: (b.__setitem__(slice(I(0), I(2)), [70]), b))(fresh()),
 lambda: (lambda b: (b.__setitem__(slice(I(0), I(2)), BS(b'Q')), b))(fresh()),
 lambda: (lambda b: (bytearray.__setitem__(b, slice(I(0), I(4), I(2)), b'xy'), b))(fresh()),
 lambda: (lambda b: (bytearray.__setitem__(b, slice(I(0), I(4), I(2)), b'xyz'), b))(fresh()),
 lambda: (lambda b: (b.__delitem__(slice(I(0), I('bad'))), b))(fresh()),
 lambda: (lambda L: (L.__setitem__(slice(I(0), I(1)), Vals()), L))([1, 2, 3]),
 lambda: (lambda L: (L.__setitem__(slice(I(0), I(3), I(2)), [9]), L))([1, 2, 3]),
 lambda: (lambda L: (list.__delitem__(L, slice(I(0), None, I(-1))), L))([1, 2, 3]),
 lambda: 'abcdef'.__getitem__(slice(I(1), I(5), I(2))),
 lambda: b'abcdef'.__getitem__(slice(I(1), None)),
 lambda: (1, 2, 3).__getitem__(slice(I(-2), None)),
 lambda: range(10).__getitem__(slice(I(1), I(2 ** 70))),
 lambda: [1, 2, 3].__getitem__(slice(I(1), None), 0),
 lambda: view().__getitem__(slice(I(1), I(4), I(2))).tobytes(),
 lambda: memoryview.__getitem__(view(), slice(I(-2), None)).tobytes(),
 lambda: view().__getitem__(slice(I('bad'), None)),
 lambda: view().__getitem__(slice(None, None, I(0))),
 lambda: (lambda v: (v.__setitem__(slice(I(1), I(3)), b'XY'), bytes(v.obj)))(view()),
 lambda: (lambda v: (v.__setitem__(slice(I(1), I(3)), b'XYZ'), bytes(v.obj)))(view()),
 lambda: (lambda v: (v.__setitem__(slice(I(0), I(4), I(2)), bytearray(b'QR')), bytes(v.obj)))(view()),
 lambda: (lambda v: (v.__setitem__(slice(I(1), I(3)), 5), bytes(v.obj)))(view()),
 lambda: (lambda v: (v.__setitem__(slice(I(1), I(3)), memoryview(b'MN')), bytes(v.obj)))(view()),
 lambda: memoryview(b'abc').__setitem__(slice(I(1), I(2)), b'Z'),
 lambda: view().__delitem__(slice(I(1), I(2))),
 lambda: (lambda v: (v.release(), v.__getitem__(slice(I(1), None))))(view()),
 lambda: memoryview(b'abcdef').cast('B', (2, 3)).__getitem__(slice(I(1), None)).tolist(),
 lambda: view().__setitem__(slice(1, 3), 'ab'),
 lambda: view().__setitem__(slice(1, 3), [1, 2]),
 lambda: on([1, 2, 3], lambda L: L.__setitem__(slice(0, 1), Items([5, 6]))),
 lambda: on([1, 2, 3], lambda L: list.__setitem__(L, slice(None, None, 2), Items([5, 6]))),
 lambda: on([1, 2, 3], lambda L: L.__setitem__(slice(None, None, 2), Items([5]))),
 lambda: on([1, 2, 3], lambda L: L.__setitem__(slice(0, 1), Items([5], True))),
 lambda: on([1, 2, 3], lambda L: L.__setitem__(slice(0, 1), gen())),
 lambda: on([1, 2, 3], lambda L: L.__setitem__(slice(I(0), I(1)), gen())),
 lambda: on([1, 2, 3], lambda L: L.__setitem__(slice(0, None, 0), Items([5]))),
 lambda: on(LS([1, 2, 3]), lambda L: L.__setitem__(slice(0, 1), Items([5]))),
 lambda: on([1, 2, 3], lambda L: L.__setitem__(slice('a', 1), Items([5]))),
 lambda: on(bytearray(b'abc'), lambda b: b.__setitem__(slice(0, 1), Items([65, 66]))),
 lambda: on(bytearray(b'abc'), lambda b: b.__setitem__(slice(0, 1), Items([65, 300]))),
 lambda: on(bytearray(b'abc'), lambda b: b.__setitem__(slice(0, 1), Items([65], True))),
 lambda: on(bytearray(b'abc'), lambda b: b.__setitem__(slice(0, 1), gen())),
 lambda: on(bytearray(b'abc'), lambda b: bytearray.__setitem__(b, slice(None, None, 2), Items([1, 2]))),
 lambda: on(bytearray(b'abc'), lambda b: b.__setitem__(slice(None, None, 2), Items([1]))),
 lambda: on(BS(b'abc'), lambda b: b.__setitem__(slice(I(0), 1), Items([65]))),
 lambda: on(bytearray(b'abc'), lambda b: b.__setitem__(slice(0, 1), Items(['x']))),
 lambda: on(bytearray(b'abc'), lambda b: (memoryview(b), b.__setitem__(slice(0, 1), Items([1, 2])))),
]
EXPECTED = [
    (('LookupError', 'bad'), ['bad']),
    (('LookupError', 'bad'), [1, 'bad']),
    (('TypeError', 'I.__index__() must return an int, not str'), ['str']),
    (('ValueError', 'slice step cannot be zero'), [0]),
    (('ValueError', 'slice step cannot be zero'), []),
    (('TypeError', 'slice indices must be integers or have an __index__ method'), []),
    (('TypeError', 'slice indices must be integers or have an __index__ method'), [1]),
    ([], [1180591620717411303424]),
    ([2, 3], [1]),
    ([2, 3], [1]),
    ((None, bytearray(b'abcdefcdef')), [0, 2, 0, 2]),
    ((None, BS(b'xyzz')), [0, 2, 0, 2]),
    (('TypeError', 'can assign only bytes, buffers, or iterables of ints in range(0, 256)'), [0, 2]),
    ((None, bytearray(b'ABcdef')), [0, 2, 'iter', 0, 2]),
    ((None, bytearray(b'Fcdef')), [0, 2, 0, 2]),
    ((None, bytearray(b'Qcdef')), [0, 2]),
    ((None, bytearray(b'xbydef')), [2, 0, 4, 2, 0, 4]),
    (('ValueError', 'attempt to assign bytes of size 3 to extended slice of size 2'), [2, 0, 4, 2, 0, 4]),
    (('LookupError', 'bad'), [0, 'bad']),
    ((None, [65, 66, 2, 3]), [0, 1, 'iter']),
    (('ValueError', 'attempt to assign sequence of size 1 to extended slice of size 2'), [2, 0, 3]),
    ((None, [2, 3]), [-1, 0]),
    ('bd', [2, 1, 5]),
    (b'bcdef', [1]),
    ((2, 3), [-2]),
    (range(1, 10), [1, 1180591620717411303424]),
    (('TypeError', 'list.__getitem__() takes exactly one argument (2 given)'), []),
    (b'bd', [2, 1, 4]),
    (b'ef', [-2]),
    (('LookupError', 'bad'), ['bad']),
    (('ValueError', 'slice step cannot be zero'), [0]),
    ((None, b'aXYdef'), [1, 3]),
    (('ValueError', 'memoryview assignment: lvalue and rvalue have different structures'), [1, 3]),
    ((None, b'QbRdef'), [2, 0, 4]),
    (('TypeError', "a bytes-like object is required, not 'int'"), []),
    ((None, b'aMNdef'), [1, 3]),
    (('TypeError', 'cannot modify read-only memory'), []),
    (('TypeError', 'cannot delete memory'), []),
    (('ValueError', 'operation forbidden on released memoryview object'), []),
    ([[100, 101, 102]], [1]),
    (('TypeError', "a bytes-like object is required, not 'str'"), []),
    (('TypeError', "a bytes-like object is required, not 'list'"), []),
    ([5, 6, 2, 3], ['iter']),
    ([5, 2, 6], ['iter']),
    (('ValueError', 'attempt to assign sequence of size 1 to extended slice of size 2'), ['iter']),
    (('LookupError', 'it'), ['iter']),
    ([7, 8, 2, 3], ['gen']),
    ([7, 8, 2, 3], [0, 1, 'gen']),
    (('ValueError', 'slice step cannot be zero'), []),
    ([5, 2, 3], ['iter']),
    (('TypeError', 'slice indices must be integers or have an __index__ method'), []),
    (bytearray(b'ABbc'), ['iter']),
    (('ValueError', 'byte must be in range(0, 256)'), ['iter']),
    (('LookupError', 'it'), ['iter']),
    (bytearray(b'\x07\x08bc'), ['gen']),
    (bytearray(b'\x01b\x02'), ['iter']),
    (('ValueError', 'attempt to assign bytes of size 1 to extended slice of size 2'), ['iter']),
    (BS(b'Abc'), [0, 'iter', 0]),
    (('TypeError', "'str' object cannot be interpreted as an integer"), ['iter']),
    (('BufferError', 'Existing exports of data: object cannot be re-sized'), ['iter']),
]
assert_eq(len(cases), len(EXPECTED))
for i, (f, expected) in enumerate(zip(cases, EXPECTED)):
    assert_eq(run(f), expected, str(i))
def g():
    b = fresh()
    b.__setitem__(slice(I(1), I(3)), b'XY')
    yield b, [1, 2, 3].__getitem__(slice(I(1), None))
assert_eq(run(lambda: list(g())), ([(bytearray(b'aXYdef'), [2, 3])], [1, 3, 1, 3, 1]))
def zero_step():
    L = [1, 2]
    L[0::0] = gen()
assert_eq(run(zero_step), (('ValueError', 'slice step cannot be zero'), []))
