# spec: PLS-315 7.2.4, 7.6.2, 25.5.2, 24.3
# description: an unsupported comparison or concatenation of a builtin subclass's instance names the operands' own types; a str, list or tuple concatenation names its built-in type on the left.
from harness import *


class I(int): pass
class St(str): pass
class L(list): pass
class T(tuple): pass
class B(bytes): pass


def message(f):
    return str(assert_raises(TypeError, f))


def messages():
    return [message(lambda: I(1) < St("a")), message(lambda: St("a") >= I(1)), message(lambda: I(1) > "a"),
            message(lambda: 1 <= L()), message(lambda: L([1]) < T((1,))),
            message(lambda: St("a") + I(1)), message(lambda: L() + T()), message(lambda: T() + 1),
            message(lambda: [] + T()), message(lambda: B(b"") + St("a")), message(lambda: b"" + I(1))]


expected = ["'<' not supported between instances of 'I' and 'St'", "'>=' not supported between instances of 'St' and 'I'",
            "'>' not supported between instances of 'I' and 'str'", "'<=' not supported between instances of 'int' and 'L'",
            "'<' not supported between instances of 'L' and 'T'",
            'can only concatenate str (not "I") to str', 'can only concatenate list (not "T") to list',
            'can only concatenate tuple (not "int") to tuple', 'can only concatenate list (not "T") to list',
            "can't concat St to B", "can't concat I to bytes"]
assert_eq(messages(), expected)

# Items compare as themselves: their own TypeError is kept.
assert_eq(message(lambda: L([1]) < L(["a"])), "'<' not supported between instances of 'int' and 'str'")


class Raises:
    def __gt__(self, other):
        raise TypeError("'<' not supported between instances of 'int' and 'list'")

    def __radd__(self, other):
        raise TypeError("can only concatenate mine")


# A Python method's TypeError is its own.
assert_eq(message(lambda: I(1) < Raises()), "'<' not supported between instances of 'int' and 'list'")
assert_eq(message(lambda: St("a") + Raises()), "can only concatenate mine")
assert_eq(message(lambda: B(b"") + Raises()), "can only concatenate mine")
