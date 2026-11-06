# spec: PLS-315 10.2.1, 20.2.5, 10.2.2
# description: Calling a class with a Python __new__ calls it with the
# class and the arguments; an instance of the class it returns is then
# initialized by its own type's __init__ with the same arguments, and
# anything else is the call's value as it is. What either raises reaches
# the caller. Each holds at module level and inside a function.
from harness import *

log = []
class A:
    def __new__(cls, *args):
        for i in range(2): pass
        log.append(('new', cls.__name__, args))
        return object.__new__(cls)
    def __init__(self, x=0, y=0):
        for i in range(2): pass
        log.append(('init', x, y))
        self.v = (x, y)
class B(A):
    pass
class Other:
    def __new__(cls, n):
        return n * 2
    def __init__(self, n): log.append('never')
class Native:
    def __new__(cls):
        return object.__new__(cls)
class I(int):
    def __new__(c, v):
        for i in range(2): pass
        return int.__new__(c, v)
class BadInit:
    def __new__(cls): return object.__new__(cls)
    def __init__(self): return 3
class Raising:
    def __new__(cls): raise KeyError('new')
class Elsewhere:
    def __new__(cls): return B(5)
def constructed():
    out = [A(1, 2).v, B().v, Other(4), type(Native()).__name__, I(3) - 3, type(I(3)).__name__]
    args = [7, 8]
    out.append(A(*args).v)
    try: BadInit()
    except TypeError as e: out.append(str(e))
    try: Raising()
    except KeyError as e: out.append(e.args)
    out.append(Elsewhere().v)
    try: A(1, 2, 3)
    except TypeError as e: out.append(str(e))
    return out
assert constructed() == [(1, 2), (0, 0), 8, "Native", 0, "I", (7, 8), "__init__() should return None, not 'int'", ("new",), (5, 0),
                         "A.__init__() takes from 1 to 3 positional arguments but 4 were given"], constructed()
assert log == [("new", "A", (1, 2)), ("init", 1, 2), ("new", "B", ()), ("init", 0, 0), ("new", "A", (7, 8)), ("init", 7, 8),
               ("new", "B", (5,)), ("init", 5, 0), ("new", "A", (1, 2, 3))], log
log.clear()
assert (A(1, 2).v, Other(1), I(2) + 1, log) == ((1, 2), 2, 3, [("new", "A", (1, 2)), ("init", 1, 2)])
