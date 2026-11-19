# spec: PLS-315 20.3.1
# description: super(type, obj), with obj neither a subclass of type nor
# an instance of one, reads obj's __class__ attribute, which a property
# may compute by looping Python code; a class that is a subclass of type
# makes the super object, any other value a TypeError, and the read's own
# error propagates. Zero-argument super() takes the same steps. Inside
# functions and generators as at module level.
from harness import *

log = []
class A:
    def f(self): return "A.f"
class B(A):
    def f(self): return "B.f+" + super().f()
class Proxy:
    @property
    def __class__(self):
        for _ in range(2): pass
        log.append("class")
        return B
class Bad:
    @property
    def __class__(self): raise LookupError("class read")
class Wrong:
    @property
    def __class__(self): return int
class Reader(A):
    @property
    def __class__(self):
        log.append("never")
        return B
    def g(self): return super().f()

def failed(obj):
    try: super(B, obj)
    except Exception as e: return "%s: %s" % (type(e).__name__, e)

def run():
    del log[:]
    s = super(B, Proxy())
    t = super(A, Proxy())
    return [s.f(), s.__thisclass__.__name__, s.__self_class__.__name__, failed(Bad()), failed(Wrong()), B().f(),
            Reader().g(), t.__self_class__.__name__, log[:]]

EXPECTED = ["A.f", "B", "B", "LookupError: class read",
            "TypeError: super(type, obj): obj (instance of Wrong) is not an instance or subtype of type (B).",
            "B.f+A.f", "A.f", "B", ["class", "class"]]

def paused():
    def gen():
        s = super(B, Proxy())
        yield s.f()
        yield B().f()
    del log[:]
    return list(gen()), log[:]

assert_eq((run(), paused()), (EXPECTED, (["A.f", "B.f+A.f"], ["class"])))
def main(): return run(), paused()
assert_eq(main(), (EXPECTED, (["A.f", "B.f+A.f"], ["class"])))
