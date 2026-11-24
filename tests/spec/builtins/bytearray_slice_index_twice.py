# spec: PLS-315 24.2, 7.5.3
# description: a store into a bytearray's slice whose part has a Python
# __index__ converts the slice, then refuses a number (an object whose
# type has __index__, __int__ or __float__, or a complex; __complex__
# alone is no number) or a str, copies any other value but a bytearray by
# bytearray(), its items' Python __index__ and a generator included, and
# converts the slice as written again; a bytearray value converts it once.
# Each Python call may loop; so does a store through __setitem__, into a
# subclass's instance, or in a generator.
from harness import assert_eq
log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass
class I:
    def __init__(self, v=0): self.v = v
    def __index__(self): spin(); log.append(('i', self.v)); return self.v
class J:
    def __index__(self): spin(); log.append('j'); return 7
class Num:
    def __index__(self): return 1
    def __iter__(self): return iter([5])
class Flo:
    def __float__(self): return 1.0
    def __iter__(self): return iter([6])
class Cx:
    def __complex__(self): return 1j
    def __iter__(self): spin(); log.append('iter'); return iter([4])
def gen():
    spin(); log.append('g'); yield 1
class Sub(bytearray): pass
def store(value, key=None, target=None):
    b = bytearray(3) if target is None else target
    del log[:]
    try: b[slice(I(), 1) if key is None else key] = value
    except Exception as e: return type(e).__name__, str(e), log[:]
    return bytes(b), log[:]
refused = "can assign only bytes, buffers, or iterables of ints in range(0, 256)"
assert_eq(store([63]), (b'?\x00\x00', [('i', 0), ('i', 0)]))
assert_eq(store([J()]), (b'\x07\x00\x00', [('i', 0), 'j', ('i', 0)]))
assert_eq(store((1, 2)), (b'\x01\x02\x00\x00', [('i', 0), ('i', 0)]))
assert_eq(store(gen()), (b'\x01\x00\x00', [('i', 0), 'g', ('i', 0)]))
assert_eq(store({2}), (b'\x02\x00\x00', [('i', 0), ('i', 0)]))
assert_eq(store(b'?'), (b'?\x00\x00', [('i', 0), ('i', 0)]))
assert_eq(store(memoryview(b'm')), (b'm\x00\x00', [('i', 0), ('i', 0)]))
assert_eq(store(bytearray(b'?')), (b'?\x00\x00', [('i', 0)]))
assert_eq(store(Cx()), (b'\x04\x00\x00', [('i', 0), 'iter', ('i', 0)]))
for value in ('x', 5, 1.5, 1j, True, Num(), Flo()):
    assert_eq(store(value), ('TypeError', refused, [('i', 0)]))
assert_eq(store([300]), ('ValueError', 'byte must be in range(0, 256)', [('i', 0)]))
assert_eq(store(None), ('TypeError', "cannot convert 'NoneType' object to bytearray", [('i', 0)]))
assert_eq(store([1], slice(I(), 1, I(0))), ('ValueError', 'slice step cannot be zero', [('i', 0)]))
assert_eq(store([9], target=Sub(2)), (b'\x09\x00', [('i', 0), ('i', 0)]))
# A store without a Python __index__ refuses numbers too.
b = bytearray(2)
for value in (Num(), Flo()):
    try: b[0:1] = value
    except TypeError as e: assert_eq(str(e), refused)
b[0:1] = Cx(); assert_eq(b, bytearray(b'\x04\x00'))
# Through __setitem__, and in a generator.
b = bytearray(2); del log[:]
bytearray.__setitem__(b, slice(I(1), 2), [J()])
assert_eq((b, log), (bytearray(b'\x00\x07'), [('i', 1), 'j', ('i', 1)]))
b = bytearray(2)
try: bytearray.__setitem__(b, slice(I(), 1), Num())
except TypeError as e: assert_eq(str(e), refused)
bytearray.__setitem__(b, slice(I(), 1), Cx()); assert_eq(b, bytearray(b'\x04\x00'))
def g(): yield store([J()])
assert_eq(list(g()), [(b'\x07\x00\x00', [('i', 0), 'j', ('i', 0)])])
