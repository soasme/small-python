# spec: PLS-315 19.3.12, 22.1.1, 22.3.1, 7.5.3
# description: dir() of an instance whose class defines a Python __dir__,
# or of a class whose metaclass does, calls it, which may loop, and lists
# and sorts what it returns, any iterable, a value that is not one raising
# TypeError; int() and float() of an instance with no __int__ or
# __float__ call its Python __index__, which may loop, its int the result,
# exact even from an int subclass, and as a float for float(), a value
# that is no int raising TypeError; __int__ comes before __index__.
# Inside functions as at module level.
from harness import *

log = []
class D:
    def __dir__(self):
        for _ in (): pass
        log.append("dir")
        return ("b", "a", "c")
class G:
    def __dir__(self):
        yield "z"; yield "y"
class Bad:
    def __dir__(self):
        for _ in (): pass
        return 5
class Meta(type):
    def __dir__(cls):
        for _ in (): pass
        return ["m2", "m1"]
class K(metaclass=Meta): pass
class X:
    def __index__(self):
        for _ in (): pass
        log.append("index")
        return 7
class B(int): pass
class XB:
    def __index__(self):
        for _ in (): pass
        return B(3)
class XS:
    def __index__(self):
        for _ in (): pass
        return "s"
class Both:
    def __int__(self): return 1
    def __index__(self): return 2
def run():
    out = [dir(D()), dir(G()), dir(K), int(X()), float(X()), type(int(XB())).__name__, int(XB()), int(Both())]
    try: dir(Bad())
    except TypeError as e: out.append(str(e))
    try: int(XS())
    except TypeError as e: out.append(str(e))
    try: float(XS())
    except TypeError as e: out.append(str(e))
    out.append(log[:])
    return out

expected = [["a", "b", "c"], ["y", "z"], ["m1", "m2"], 7, 7.0, "int", 3, 1,
            "'int' object is not iterable", "XS.__index__() must return an int, not str",
            "XS.__index__() must return an int, not str", ["dir", "index", "index"]]
assert_eq(run(), expected)
log.clear()
assert_eq((dir(D()), int(X()), float(X())), (["a", "b", "c"], 7, 7.0))
assert_eq(log, ["dir", "index", "index"])
