# spec: PLS-315 19.3.21, 19.3.22, 7.5.1
# description: isinstance() and issubclass() search a nested tuple's items
# depth first, before the items after it, calling each Python
# __instancecheck__ or __subclasscheck__ it reaches, which may loop, until
# one is true; the truth of a check's result is its Python __bool__, or
# __len__, once, which may loop too. A __bool__ returning other than a
# bool is a TypeError, an exception from either propagates, and deep
# nesting of tuples is searched. Plain and starred calls, inside functions
# as at module level.
from harness import *

log = []

class Truth:
    def __init__(self, v): self.v = v
    def __bool__(self):
        for _ in (): pass
        log.append(("bool", self.v))
        if self.v is None: raise LookupError("bool")
        return self.v

class Sized:
    def __init__(self, n): self.n = n
    def __len__(self):
        for _ in (): pass
        log.append(("len", self.n))
        return self.n

def meta(result):
    class M(type):
        def __instancecheck__(cls, x):
            for _ in (): pass
            log.append(("inst", cls.__name__))
            return result
        def __subclasscheck__(cls, x):
            for _ in (): pass
            log.append(("sub", cls.__name__))
            return result
    return M

Yes = meta(Truth(True))("Yes", (), {})
No = meta(Truth(False))("No", (), {})
Empty = meta(Sized(0))("Empty", (), {})
Full = meta(Sized(2))("Full", (), {})
Bad = meta(Truth(1))("Bad", (), {})
Raises = meta(Truth(None))("Raises", (), {})

class Pair(tuple): pass

def checks():
    args = (1, (No, (Empty,), Pair((Full, Yes))))
    return [isinstance(1, Yes), isinstance(1, ((No,), ((Empty,),), Full)), issubclass(int, (No, (Yes,))),
            isinstance(1, (No, Pair((Empty, Pair((No,)))))), isinstance(1, ((), (int,))), isinstance(*args),
            issubclass(int, ((((Empty,),),),))]

expected = [True, True, True, False, True, True, False]
expected_log = [("inst", "Yes"), ("bool", True),
                ("inst", "No"), ("bool", False), ("inst", "Empty"), ("len", 0), ("inst", "Full"), ("len", 2),
                ("sub", "No"), ("bool", False), ("sub", "Yes"), ("bool", True),
                ("inst", "No"), ("bool", False), ("inst", "Empty"), ("len", 0), ("inst", "No"), ("bool", False),
                ("inst", "No"), ("bool", False), ("inst", "Empty"), ("len", 0), ("inst", "Full"), ("len", 2),
                ("sub", "Empty"), ("len", 0)]
assert_eq(checks(), expected)
assert_eq(log, expected_log)
log.clear()

assert_eq((isinstance("s", ((No,), Yes)), issubclass(str, Full)), (True, True))
assert_eq(log, [("inst", "No"), ("bool", False), ("inst", "Yes"), ("bool", True), ("sub", "Full"), ("len", 2)])

deep = Yes
for _ in range(3000): deep = (deep,)
assert_eq(isinstance(1, deep), True)
log.clear()

def errors():
    out = []
    for make in (lambda: isinstance(1, (No, Bad)), lambda: issubclass(int, ((Raises,),)), lambda: isinstance(1, (No, (Raises, Yes)))):
        try: out.append(make())
        except LookupError as e: out.append(e.args)
        except TypeError as e: out.append(str(e))
    return out

assert_eq(errors(), ["Truth.__bool__() must return a bool, not int", ("bool",), ("bool",)])
assert_eq(log, [("inst", "No"), ("bool", False), ("inst", "Bad"), ("bool", 1), ("sub", "Raises"), ("bool", None),
                ("inst", "No"), ("bool", False), ("inst", "Raises"), ("bool", None)])
