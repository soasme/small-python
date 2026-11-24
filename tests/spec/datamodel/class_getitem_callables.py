# spec: PLS-315 7.8.1, 16.4
# description: A __class_getitem__ classmethod wrapping a class or a
# callable instance, rather than a function, is called with the class and
# the item: the class's Python __new__ and __init__, or the instance's
# Python __call__, which may loop, run as for a call; their exceptions
# propagate.
from harness import *

log = []
def spin():
    for _ in range(2): pass
class Alias:
    def __init__(self, origin, item):
        spin(); log.append(("init", origin.__name__, item))
        self.origin, self.item = origin, item
class Fails:
    def __new__(cls, origin, item):
        spin(); raise LookupError(item)
class Maker:
    def __call__(self, origin, item):
        spin(); log.append(("call", origin.__name__, item)); return item * 2
class A:
    __class_getitem__ = classmethod(Alias)
class B(A): pass
class C:
    __class_getitem__ = classmethod(Maker())
class D:
    __class_getitem__ = classmethod(Fails)

def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def cases():
    return [run(lambda: (A[int].origin.__name__, A[int].item)), run(lambda: B["k"].origin.__name__),
            run(lambda: C[3]), run(lambda: D["x"])]
expected = [(("A", int), [("init", "A", int), ("init", "A", int)]), ("B", [("init", "B", "k")]),
            (6, [("call", "C", 3)]), (("LookupError", "x"), [])]
assert_eq(cases(), expected)
assert_eq(run(lambda: C[4]), (8, [("call", "C", 4)]))
