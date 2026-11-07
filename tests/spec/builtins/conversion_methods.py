# spec: PLS-315 22.1.1, 22.3.1, 7.5.7, 19.3.18
# description: int(), float() and hash() of an instance call its class's
# __int__, __float__ or __hash__, which may loop, inside functions as at
# module level, and check the result: an int, a float, an integer hash with
# -1 read as -2; with no method, __index__ or the default hash answers.
from harness import *

class Number:
    def __init__(self, value): self.value = value
    def __int__(self):
        for _ in range(2): pass
        return self.value
    def __float__(self):
        for _ in range(2): pass
        return self.value
    def __hash__(self):
        for _ in range(2): pass
        return self.value
class Indexed:
    def __index__(self): return 7
class Derived(Number): pass
class Unhashable:
    __hash__ = None

def results():
    out = [int(Number(3)), float(Number(2.5)), hash(Number(5)), hash(Number(-1)),
           hash(Number(2 ** 64)) == hash(2 ** 64), int(Derived(4)), int(Indexed()), float(Indexed())]
    for f, value in ((int, 1.5), (float, 1), (hash, "a"), (hash, 1.5)):
        try:
            f(Number(value))
        except TypeError as e:
            out.append(str(e))
    try:
        hash(Unhashable())
    except TypeError as e:
        out.append(str(e))
    plain = object()
    out.append(hash(plain) == hash(plain))
    return out

expected = [3, 2.5, 5, -2, True, 4, 7, 7.0,
            "Number.__int__() must return an int, not float",
            "Number.__float__() must return a float, not int",
            "__hash__ method should return an integer",
            "__hash__ method should return an integer",
            "unhashable type: 'Unhashable'", True]
assert_eq(results(), expected)
assert_eq([type(x) for x in results()[:3]], [int, float, int])
