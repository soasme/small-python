# spec: PLS-315 24.1.3, 24.2
# description: bytes.fromhex and bytearray.fromhex called on a subclass
# call it with the bytes they made (a bytearray only for bytearray itself), its Python __new__ or
# __init__ included, and return the call's result whatever it is; errors
# pass out, and a subclass's fromhex works as a key function and in a
# generator.
from harness import assert_eq
log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass
class B(bytes):
    def __new__(cls, value):
        spin(); log.append(('new', type(value).__name__, value)); return bytes.__new__(cls, value + b'!')
class A(bytearray):
    def __init__(self, value):
        spin(); log.append(('init', type(value).__name__, bytes(value))); bytearray.__init__(self, value)
class Bad(bytes):
    def __new__(cls, value): spin(); raise KeyError(value)
class Odd(bytearray):
    def __new__(cls, value): spin(); return 'odd'
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return type(r).__name__, r, log[:]
assert_eq(run(lambda: B.fromhex('1a 2b')), ('B', b'\x1a+!', [('new', 'bytes', b'\x1a+')]))
assert_eq(run(lambda: A.fromhex('1a')), ('A', bytearray(b'\x1a'), [('init', 'bytes', b'\x1a')]))
assert_eq(run(lambda: Bad.fromhex('00')), ('tuple', ('KeyError', "b'\\x00'"), []))
assert_eq(run(lambda: Odd.fromhex('00')), ('str', 'odd', []))
assert_eq(run(lambda: B.fromhex('zz')), ('tuple', ('ValueError', 'non-hexadecimal number found in fromhex() arg at position 0'), []))
assert_eq(run(lambda: bytearray.fromhex('ff')), ('bytearray', bytearray(b'\xff'), []))
def g(): yield run(lambda: A.fromhex('41'))
assert_eq(list(g()), [('A', bytearray(b'A'), [('init', 'bytes', b'A')])])
class HexB(bytes): pass
assert_eq(sorted(["02", "01"], key=HexB.fromhex), ["01", "02"])
assert_eq([type(v).__name__ for v in map(HexB.fromhex, ["00"])], ["HexB"])
