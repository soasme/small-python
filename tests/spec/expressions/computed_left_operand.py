# spec: PLS-315 13.7, 13.10, 13.17, 15.1, 15.6
# description: An operator whose left operand is itself an operator and
# whose right one is a name, literal, item or attribute evaluates the left
# operand before the right one, each once, and calls each special method
# once, as a returned value and as a test, when operands change from
# numbers to objects between calls.
from harness import *

calls = []


class Logged:
    def __init__(self, value):
        self.value = value

    def __add__(self, other):
        calls.append("add")
        return Logged(self.value + other)

    def __mod__(self, other):
        calls.append("mod")
        return Logged(self.value % other)

    def __mul__(self, other):
        calls.append("mul")
        return self.value * other

    def __eq__(self, other):
        calls.append("eq")
        return Truth(self.value == other)

    __hash__ = None


class Truth:
    def __init__(self, value):
        self.value = value

    def __bool__(self):
        calls.append("bool")
        return self.value


class Holder:
    @property
    def right(self):
        calls.append("right")
        return 3


def scaled(x):
    return (x + 1) * 2


def odd(x):
    if x % 2 == 1:
        return True
    return False


def evens(values):
    out = []
    for i in range(len(values)):
        if values[i] % 2 == 0:
            out.append(i)
    return out


def minus(x, holder):
    return (x + 1) - holder.right


assert_same(scaled(3), 8)
assert_same(scaled(2.5), 7.0)
assert_same(odd(5), True)
assert_same(odd(4), False)
assert_same(evens([4, 3, 2.0, 1]), [0, 2])

holder = Holder()
assert_same(minus(4, holder), 2)
assert_same(calls, ["right"])
del calls[:]

assert_same(scaled(Logged(3)), 8)
assert_same(calls, ["add", "mul"])
del calls[:]
assert_same(odd(Logged(5)), True)
assert_same(calls, ["mod", "eq", "bool"])
del calls[:]
assert_same(evens([Logged(4), 3]), [0])
assert_same(calls, ["mod", "eq", "bool"])
del calls[:]


def concatenated(s):
    return (s + "b") + "c"


assert_same(concatenated("a"), "abc")
assert_raises(TypeError, concatenated, 1)


def missing(x):
    return (x + 1) + absent


assert_raises(NameError, missing, 1)


def divided(x):
    return (x + 1) // 0


assert_raises(ZeroDivisionError, divided, 1)


def compared(x):
    if (x - 1) < 0:
        return "negative"
    return "not negative"


assert_same(compared(0), "negative")
assert_same(compared(1), "not negative")
assert_raises(TypeError, compared, "a")


def remainder(x):
    if (x + 1) % 2:
        return "odd"
    return "even"


assert_same(remainder(2), "odd")
assert_same(remainder(1), "even")
assert_same(remainder(1.5), "odd")
