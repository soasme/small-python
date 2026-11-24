# spec: PLS-315 7.6.3, 14.3
# description: x *= y of a list or bytearray subclass calls its own Python
# __mul__ before y's reflected method; when both decline, the inherited
# repetition updates x in place, and a count that is no index is reported
# as a sequence's repetition; at module level and in a function.
from harness import assert_eq
class Ix:
    def __index__(self): return 2
class R:
    def __rmul__(self, o): return 'rmul'
class Mul(list):
    def __mul__(self, n): return 'mul'
class MulChild(Mul): pass
class NoMul(list):
    def __mul__(self, n): return NotImplemented
class NoMulBytes(bytearray):
    def __mul__(self, n): return NotImplemented
def run():
    out = []
    x = Mul([1]); x *= 2; out.append(x)
    x = MulChild([1]); x *= 2; out.append(x)
    x = Mul([1]); x *= R(); out.append(x)
    x = NoMul([1]); x *= R(); out.append(x)
    for make in (lambda: NoMul([1]), lambda: NoMulBytes(b'a')):
        for count in (2, Ix(), 0, -1, True, 'a'):
            x = make(); before = id(x)
            try:
                x *= count
            except TypeError as e:
                out.append(str(e)); continue
            out.append((type(x).__name__, list(x), id(x) == before))
    x = [1]
    try:
        x *= 'a'
    except TypeError as e:
        out.append(str(e))
    return out
expected = ['mul', 'mul', 'mul', 'rmul',
            ('NoMul', [1, 1], True), ('NoMul', [1, 1], True), ('NoMul', [], True),
            ('NoMul', [], True), ('NoMul', [1], True), "can't multiply sequence by non-int of type 'str'",
            ('NoMulBytes', [97, 97], True), ('NoMulBytes', [97, 97], True), ('NoMulBytes', [], True),
            ('NoMulBytes', [], True), ('NoMulBytes', [97], True), "can't multiply sequence by non-int of type 'str'",
            "can't multiply sequence by non-int of type 'str'"]
assert_eq(run(), expected)
module_out = []
x = NoMul([5]); x *= Ix(); module_out.append(x)
x = Mul([5]); x *= 3; module_out.append(x)
assert_eq(module_out, [[5, 5], 'mul'])
