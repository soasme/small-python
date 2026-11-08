# spec: PLS-315 10.2.1, 10.2.2
# description: Calling a class with keyword arguments whose class defines a
# Python __new__, which may loop, passes the class and every argument to it,
# then initializes a returned instance of the class, of its own type, with
# the same arguments, by a Python __init__ or object's, which accepts them;
# other results are returned without one, and argument errors name
# __new__, inside functions as at module level.
from harness import *

log = []
def spin():
    for _ in range(2): pass
class A:
    def __new__(cls, x=1, **kw):
        spin()
        log.append(("new", cls.__name__, x, kw))
        return super().__new__(cls)
    def __init__(self, x=1, **kw):
        spin()
        log.append(("init", x, kw))
class B:
    def __new__(cls, *args, **kw):
        spin()
        log.append(("newB", args, kw))
        return 7
class C:
    def __new__(cls, x):
        spin()
        return object.__new__(cls)
class D(A): pass
class E:
    def __new__(cls, **kw):
        spin()
        return super().__new__(cls)
    def __init__(self, **kw): self.kw = kw
def run():
    a = A(x=2, y=3)
    b = B(1, z=2)
    c = C(x=5)
    d = D(4, w=1)
    e = E(k=1)
    log.append(e.kw)
    try: C(y=1)
    except TypeError as e: log.append(str(e))
    try: A(1, x=2)
    except TypeError as e: log.append(str(e))
    out = [type(a).__name__, b, type(c).__name__, type(d).__name__, list(log)]
    del log[:]
    return out

expected = ["A", 7, "C", "D", [("new", "A", 2, {"y": 3}), ("init", 2, {"y": 3}), ("newB", (1,), {"z": 2}),
                               ("new", "D", 4, {"w": 1}), ("init", 4, {"w": 1}), {"k": 1},
                               "C.__new__() got an unexpected keyword argument 'y'",
                               "A.__new__() got multiple values for argument 'x'"]]

def main():
    return run()

assert_eq(main(), expected)
assert_eq(run(), expected)
