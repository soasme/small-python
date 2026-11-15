# spec: PLS-315 29.9.1, 13.4
# description: The first subscript of a builtin generic class in a
# program, inside a generator suspended between its operands' evaluation
# and later resumed, evaluates each operand once, in order, and gives the
# GenericAlias; later ones, a union of classes, a generic class, a type
# alias and a generic function, then behave as usual. Inside functions as
# at module level.
from harness import *

log = []

def note(value):
    log.append(value)
    return value

def gen():
    alias = note(list)[(yield "paused") or note(int)]
    yield alias

def uses():
    g = gen()
    out = [next(g), repr(g.send(None)), list(log)]
    def f[T](x: T) -> T: return x
    class C[T]: pass
    type A = dict[str, int]
    out += [repr(int | None), [p.__name__ for p in f.__type_params__], [p.__name__ for p in C.__type_params__],
            repr(A.__value__), repr(C[int])]
    return out

expected = ["paused", "list[int]", [list, int], "int | None", ["T"], ["T"], "dict[str, int]", "__main__.uses.<locals>.C[int]"]

def main():
    del log[:]
    return uses()

assert_eq(main(), expected)
del log[:]
assert_eq(uses(), expected)
