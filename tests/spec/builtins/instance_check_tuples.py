# spec: PLS-315 19.3.21, 19.3.22
# description: isinstance() and issubclass() of a tuple check its items in
# order, a class's by its metaclass's Python __instancecheck__ or
# __subclasscheck__, whose result's truth decides, until one is true; an
# exact class needs no hook, an item that is no class raises TypeError
# once reached, an error from a hook propagates, and issubclass() of a
# non-class raises TypeError at a plain item; inside functions as at
# module level.
from harness import *

log = []
class Meta(type):
    def __instancecheck__(cls, x):
        for i in range(1): pass
        log.append(("ic", cls.__name__, x)); return cls.__name__ == "Yes"
    def __subclasscheck__(cls, x):
        log.append(("sc", cls.__name__)); return cls.__name__ == "Yes"
class No(metaclass=Meta): pass
class Yes(metaclass=Meta): pass
class Bad(metaclass=Meta):
    pass
class R(type):
    def __instancecheck__(cls, x): raise KeyError("r")
class Raise(metaclass=R): pass
class T:
    def __bool__(self): log.append("bool"); return False
class Q(type):
    def __instancecheck__(cls, x): return T()
class Odd(metaclass=Q): pass
def checks():
    out = [isinstance(1, (No, Yes, int)), isinstance(1, (No, str)), isinstance(1, (int, No)), isinstance(No(), (No,)),
           issubclass(int, (No, Yes)), issubclass(bool, (No, int)), isinstance(1, (Odd, No)), isinstance(1, ((No, Yes),))]
    for args in ((1, (No, 5)), (1, (Raise, int)), (1, ())):
        try: out.append(isinstance(*args))
        except Exception as e: out.append(type(e).__name__ + ": " + str(e))
    for cls in ((No, int), (int, No)):
        try: out.append(issubclass(1, cls))
        except Exception as e: out.append(type(e).__name__ + ": " + str(e))
    out.append(log[:])
    del log[:]
    return out

expected = [True, False, True, True, True, True, False, True,
            "TypeError: isinstance() arg 2 must be a type, a tuple of types, or a union", "KeyError: 'r'", False,
            "TypeError: issubclass() arg 1 must be a class", "TypeError: issubclass() arg 1 must be a class",
            [("ic", "No", 1), ("ic", "Yes", 1), ("ic", "No", 1), ("sc", "No"), ("sc", "Yes"), ("sc", "No"), "bool",
             ("ic", "No", 1), ("ic", "No", 1), ("ic", "Yes", 1), ("ic", "No", 1), ("sc", "No")]]
assert_eq(checks(), expected)
assert_eq([isinstance(1, (No, Yes)), log], [True, [("ic", "No", 1), ("ic", "Yes", 1)]])
