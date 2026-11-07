# spec: PLS-315 19.3.21, 19.3.22
# description: isinstance and issubclass with a class whose metaclass
# defines a Python __instancecheck__ or __subclasscheck__ call it once with
# the class and the tested object, the result's truth their bool and its
# exception theirs; isinstance of an instance of exactly that class calls
# none. Methods that loop run in function statements, with arguments that
# need evaluating or not, as at module level.
from harness import *

log = []

class Falsy:
    def __bool__(self): return False

class Raising:
    def __bool__(self): raise KeyError("truth")

class Meta(type):
    def __instancecheck__(cls, obj):
        for _ in range(2): pass
        log.append(("i", cls.__name__, obj))
        if obj == "raise": raise ValueError("check")
        if obj == "truth": return Raising()
        return Falsy() if obj == 0 else obj == 1 or []
    def __subclasscheck__(cls, sub):
        for _ in range(2): pass
        log.append(("s", cls.__name__, sub.__name__))
        if sub is bool: raise KeyError("bad")
        return 1

class A(metaclass=Meta): pass

class Arity(type):
    def __instancecheck__(cls): return True

class B(metaclass=Arity): pass

def error(f, *args):
    try:
        f(*args)
    except Exception as e:
        return type(e).__name__, str(e)

def one(): return 1

def checks():
    del log[:]
    out = [isinstance(1, A), isinstance(2, A), isinstance(0, A), isinstance(A(), A),
           isinstance(one(), A), isinstance(one() + 1, A),
           issubclass(int, A), issubclass(A, A), issubclass(type(one()), A)]
    if isinstance(1, A): out.append("yes")
    out.append([isinstance(x, A) for x in (1, 3)])
    try: isinstance("raise", A)
    except ValueError as e: out.append(str(e))
    try: isinstance("truth", A)
    except KeyError as e: out.append(str(e))
    try: issubclass(bool, A)
    except KeyError as e: out.append(str(e))
    try: isinstance(1, B)
    except TypeError as e: out.append(str(e))
    try: isinstance(one(), B)
    except TypeError as e: out.append(str(e))
    out.append(list(log))
    return out

arity = "Arity.__instancecheck__() takes 1 positional argument but 2 were given"
expected = [True, False, False, True, True, False, True, True, True, "yes", [True, False],
            "check", "'truth'", "'bad'", arity, arity,
            [("i", "A", 1), ("i", "A", 2), ("i", "A", 0), ("i", "A", 1), ("i", "A", 2),
             ("s", "A", "int"), ("s", "A", "A"), ("s", "A", "int"), ("i", "A", 1),
             ("i", "A", 1), ("i", "A", 3), ("i", "A", "raise"), ("i", "A", "truth"), ("s", "A", "bool")]]
assert_eq(checks(), expected)
assert_eq(checks(), expected)
del log[:]
assert_eq([isinstance(1, A), isinstance(5, A), issubclass(str, A), error(isinstance, 1, B)],
          [True, False, True, ("TypeError", arity)])
assert_eq(log, [("i", "A", 1), ("i", "A", 5), ("s", "A", "str")])
