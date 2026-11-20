# spec: PLS-315 10.4.2, 7.3.6
# description: a class's __doc__ is that of its namespace read through
# its __get__(None, C) when the descriptor's class defines one, which may
# loop; an instance's reads it with the instance; a subclass's own
# __doc__ is None; a metaclass's non-data __doc__ does not hide the
# class's, and its property does. Its exception propagates. Inside
# functions as at module level.
from harness import *

class D:
    def __get__(self, o, t):
        for _ in (): pass
        if t.__name__ == "E": raise LookupError("doc")
        return (o is None, t.__name__)

class N:
    __doc__ = D()
class Sub(N): pass
class MS(type):
    __doc__ = "meta text"
class X(metaclass=MS):
    __doc__ = D()
class MD(type):
    @property
    def __doc__(cls):
        for _ in (): pass
        return "meta prop"
class Y(metaclass=MD):
    __doc__ = D()
class E:
    __doc__ = D()

def reads():
    try: E.__doc__
    except LookupError as e: err = str(e)
    return [N.__doc__, N().__doc__, Sub.__doc__, Sub().__doc__, X.__doc__, Y.__doc__, Y().__doc__, err]

expected = [(True, "N"), (False, "N"), None, None, (True, "X"), "meta prop", (False, "Y"), "doc"]
assert_eq(reads(), expected)
assert_eq([N.__doc__, X.__doc__, Y.__doc__], [(True, "N"), (True, "X"), "meta prop"])
