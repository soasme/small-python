# spec: PLS-315 7.5.4, 14.2, 24.2, 25.4.2
# description: A slice assignment to a bytearray, a subclass's instance
# too, of a value whose Python __iter__ or generator gives its bytes
# converts the slice's parts by their Python __index__, refusing a zero
# step, then copies the value to a bytearray, then converts the slice
# again before the store; the same through a subclass's own __setitem__
# calling bytearray.__setitem__, in a chained assignment, a for target,
# exec() and a generator.
from harness import assert_eq

log = []
class I:
    def __init__(self, v): self.v = v
    def __index__(self):
        for _ in (): pass
        log.append(self.v); return self.v
class Items:
    def __init__(self, items, fail=False): self.items = items; self.fail = fail
    def __iter__(self):
        for _ in (): pass
        log.append('iter')
        if self.fail: raise LookupError('it')
        return iter(self.items)
class BS(bytearray): pass
class Own(bytearray):
    def __setitem__(self, k, v):
        log.append('own'); bytearray.__setitem__(self, k, v)
def gen():
    log.append('gen'); yield 70; yield 71
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def s1(b): b[0:2] = Items([65, 66]); return b
def s2(b): b[I(0):I(2)] = Items([65]); return b
def s3(b): b[::2] = gen(); return b
def s4(b): b[::I(2)] = Items([1]); return b
def s5(b): b[0:1] = Items([300]); return b
def s6(b): b[0:1] = Items([], True); return b
def s7(b): b[0:1] = x = Items([66]); return b, type(x).__name__
def s8(b):
    for b[0:1] in [Items([67])]: pass
    return b
def s9(b): b[I(0):I(1)] = Items(['q']); return b
def s10(b): m = memoryview(b); b[0:1] = Items([1, 2]); return b
def s11(b): b[0:0:0] = Items([1]); return b
def s12(b):
    exec("b[0:1] = Items([90])", {'b': b, 'Items': Items}); return b
cases = [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12]
EXPECTED = [
    (bytearray(b'ABc'), ['iter']),
    (BS(b'ABc'), ['iter']),
    (Own(b'ABc'), ['own', 'iter']),
    (bytearray(b'Ac'), [0, 2, 'iter', 0, 2]),
    (BS(b'Ac'), [0, 2, 'iter', 0, 2]),
    (Own(b'Ac'), ['own', 0, 2, 'iter', 0, 2]),
    (bytearray(b'FbG'), ['gen']),
    (BS(b'FbG'), ['gen']),
    (Own(b'FbG'), ['own', 'gen']),
    (('ValueError', 'attempt to assign bytes of size 1 to extended slice of size 2'), [2, 'iter', 2]),
    (('ValueError', 'attempt to assign bytes of size 1 to extended slice of size 2'), [2, 'iter', 2]),
    (('ValueError', 'attempt to assign bytes of size 1 to extended slice of size 2'), ['own', 2, 'iter', 2]),
    (('ValueError', 'byte must be in range(0, 256)'), ['iter']),
    (('ValueError', 'byte must be in range(0, 256)'), ['iter']),
    (('ValueError', 'byte must be in range(0, 256)'), ['own', 'iter']),
    (('LookupError', 'it'), ['iter']),
    (('LookupError', 'it'), ['iter']),
    (('LookupError', 'it'), ['own', 'iter']),
    ((bytearray(b'Bbc'), 'Items'), ['iter']),
    ((BS(b'Bbc'), 'Items'), ['iter']),
    ((Own(b'Bbc'), 'Items'), ['own', 'iter']),
    (bytearray(b'Cbc'), ['iter']),
    (BS(b'Cbc'), ['iter']),
    (Own(b'Cbc'), ['own', 'iter']),
    (('TypeError', "'str' object cannot be interpreted as an integer"), [0, 1, 'iter']),
    (('TypeError', "'str' object cannot be interpreted as an integer"), [0, 1, 'iter']),
    (('TypeError', "'str' object cannot be interpreted as an integer"), ['own', 0, 1, 'iter']),
    (('BufferError', 'Existing exports of data: object cannot be re-sized'), ['iter']),
    (('BufferError', 'Existing exports of data: object cannot be re-sized'), ['iter']),
    (('BufferError', 'Existing exports of data: object cannot be re-sized'), ['own', 'iter']),
    (('ValueError', 'slice step cannot be zero'), []),
    (('ValueError', 'slice step cannot be zero'), []),
    (('ValueError', 'slice step cannot be zero'), ['own']),
    (bytearray(b'Zbc'), ['iter']),
    (BS(b'Zbc'), ['iter']),
    (Own(b'Zbc'), ['own', 'iter']),
]
results = [run(lambda: f(t(b'abc'))) for f in cases for t in (bytearray, BS, Own)]
assert_eq(len(results), len(EXPECTED))
for i, (got, expected) in enumerate(zip(results, EXPECTED)):
    assert_eq(got, expected, str(i))
def g():
    b = bytearray(b'xyz')
    b[I(0):1] = Items([75])
    yield b
assert_eq(run(lambda: list(g())), ([bytearray(b'Kyz')], [0, 'iter', 0]))
