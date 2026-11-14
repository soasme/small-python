# spec: PLS-315 7.6.2
# description: an operand of a builtin type's subclass that does not define
# an operator method uses the builtin's own in that method's place, in the
# method's turn; a subclass defining the method loses the builtin's result
# when the method declines, while a sequence's concatenation and
# repetition, which come after both operands' methods, stay unless the
# class defines the method; a str subclass reaches str's __add__ in its own
# turn only when it defines __radd__; inside functions as at module level.
from harness import *

class P(int): pass
class I(int):
    def __radd__(self, o): return "radd"
    def __rmul__(self, o): return "rmul"
class N(int):
    def __add__(self, o): return NotImplemented
    def __rmul__(self, o): return NotImplemented
class S(str):
    def __mul__(self, o): return NotImplemented
    def __rmul__(self, o): return NotImplemented
    def __add__(self, o): return NotImplemented
class L(list):
    def __add__(self, o): return NotImplemented
    def __radd__(self, o): return NotImplemented
class F(float): pass
class A(str): __radd__ = lambda s, o: "A"
class B(str): __radd__ = lambda s, o: "B"
class C(str): pass

def results():
    return [P(2) + I(1), I(1) + P(2), P(2) * I(3), 2 + I(1), P(2) + 1.5,
            "ab" * N(2), N(2) + 3, 3 + N(2), "b" + S("a"), [2] + L([1]),
            F(1.5) + I(1), P(7) % I(4), divmod(P(7), I(2)), pow(P(2), I(3)),
            P(2) ** I(3), P(1) < I(2), P(5) - P(2), A("a") + B("b"),
            C("a") + B("b")]

expected = [3, 3, 6, "radd", 3.5, "abab", 5, 5, "ba", [2, 1], 2.5, 3,
            (3, 1), 8, 8, True, 3, "ab", "B"]
assert_eq(results(), expected)
assert_eq([type(r) for r in results()[:3]], [int, int, int])

def errors():
    out = []
    for f in (lambda: P(2) + "s", lambda: S("a") * 2, lambda: 2 * S("a"),
              lambda: N(2) + N(3), lambda: S("a") + "b", lambda: L([1]) + [2]):
        try: f()
        except TypeError as e: out.append(str(e))
    return out

assert_eq(errors(), [
    "unsupported operand type(s) for +: 'P' and 'str'",
    "unsupported operand type(s) for *: 'S' and 'int'",
    "unsupported operand type(s) for *: 'int' and 'S'",
    "unsupported operand type(s) for +: 'N' and 'N'",
    "unsupported operand type(s) for +: 'S' and 'str'",
    "unsupported operand type(s) for +: 'L' and 'list'",
])
assert_eq(A("a") + B("b"), "ab")
