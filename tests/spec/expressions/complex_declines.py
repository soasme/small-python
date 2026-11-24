# spec: PLS-315 7.6.2, 7.6.3
# description: a complex number's operator methods decline an operand that
# is no number, so a sequence repeats by it or concatenates with it under
# the sequence's own messages, and any other operand reaches the operator's
# unsupported-operand error; in place too.
from harness import assert_eq
def error(f):
    try:
        f()
    except TypeError as e:
        return str(e)
def augment(x, y):
    x *= y
assert_eq((1j).__mul__("b"), NotImplemented)
assert_eq([error(lambda: "b" * 1j), error(lambda: 1j * [1]), error(lambda: augment(1j, (1,)))],
          ["can't multiply sequence by non-int of type 'complex'"] * 3)
assert_eq(error(lambda: "b" + 1j), 'can only concatenate str (not "complex") to str')
assert_eq([error(lambda: 1j + "b"), error(lambda: 1j - [1]), error(lambda: None * 1j),
           error(lambda: 1j ** "b")],
          ["unsupported operand type(s) for +: 'complex' and 'str'",
           "unsupported operand type(s) for -: 'complex' and 'list'",
           "unsupported operand type(s) for *: 'NoneType' and 'complex'",
           "unsupported operand type(s) for ** or pow(): 'complex' and 'str'"])
class R:
    def __rmul__(self, o): return 'rmul'
assert_eq(1j * R(), 'rmul')
assert_eq((1j * 2, 2.0 * 1j, 1j * True), (2j, 2j, 1j))
