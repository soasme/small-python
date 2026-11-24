# spec: PLS-315 24.3, 7.6.3
# description: a bytes or bytearray concatenation with an operand that is
# not bytes-like names both operands' own types, a subclass's instance's
# type included, by +, +=, and an explicit __iadd__.
from harness import assert_eq
def error(f):
    try:
        f()
    except TypeError as e:
        return str(e)
def augment(x, y):
    x += y
    return x
class BP(bytearray): pass
class BN(bytearray):
    def __add__(self, o): return NotImplemented
class R:
    def __radd__(self, o): return NotImplemented
assert_eq([error(lambda: augment(BP(b'a'), 1)), error(lambda: augment(BN(b'a'), R())), error(lambda: augment(BN(b'a'), 'b')),
           error(lambda: BP(b'a').__iadd__(1)), error(lambda: BP(b'a') + 1), error(lambda: augment(bytearray(b'a'), R())),
           error(lambda: b'a' + 'b')],
          ["can't concat int to BP", "can't concat R to BN", "can't concat str to BN", "can't concat int to BP",
           "can't concat int to BP", "can't concat R to bytearray", "can't concat str to bytes"])
assert_eq((augment(BN(b'a'), b'b'), augment(BP(b'a'), bytearray(b'c'))), (BN(b'ab'), BP(b'ac')))
