# spec: PLS-315 7.3.2, 7.2.4, 13.6
# description: An operator's special method that its class holds as a
# descriptor is read first, by the class's Python __get__ given the
# descriptor, the operand and its class, or a property's getter given the
# operand, then what the read returns is called with the other operand:
# for binary operators, their reflected forms, comparisons, != by __eq__,
# augmented assignment, unary operators and subscription. A read that
# raises AttributeError leaves the method absent where the operation has a
# fallback, and its error propagates elsewhere; the read and the call may
# loop and pause in a generator; what a read returns may be a bound
# method, a callable instance or a builtin. Inside functions as at module
# level.
from harness import *

log = []
class Desc:
    def __init__(self, name, result=None): self.name, self.result = name, result
    def __get__(self, obj, owner):
        for _ in range(2): pass
        log.append(("get", self.name, type(obj).__name__, owner.__name__))
        name, result = self.name, self.result
        def method(*args):
            for _ in range(2): pass
            log.append((name, len(args)))
            return result if result is not None else (name, args)
        return method
class Declines:
    def __get__(self, obj, owner):
        for _ in range(2): pass
        log.append("declines")
        return lambda other: NotImplemented
class Called:
    def __call__(self, other):
        for _ in range(2): pass
        log.append("called")
        return ("called", other)
class GivesCallable:
    def __get__(self, obj, owner): return Called()
class GivesBuiltin:
    def __get__(self, obj, owner): return len
class Bound:
    def __get__(self, obj, owner): return obj.mul
class A:
    __add__ = Desc("add")
    __radd__ = Desc("radd")
    __eq__ = Desc("eq", "EQ")
    __lt__ = Desc("lt", True)
    __neg__ = Desc("neg")
    __getitem__ = Desc("getitem")
    __iadd__ = Desc("iadd")
    __sub__ = GivesCallable()
    __mul__ = Bound()
    __and__ = GivesBuiltin()
    def mul(self, other):
        for _ in range(2): pass
        return ("mul", other)
class B:
    __eq__ = Declines()
class N:
    __eq__ = Desc("eq", False)

def booh(self):
    for _ in range(2): pass
    raise AttributeError("booh")
def boom(self):
    for _ in range(2): pass
    raise KeyError("boom")
def holder(name, getter): return type("E", (), {name: property(getter)})
def attempt(f):
    try: return f()
    except Exception as e: return type(e).__name__ + ": " + str(e)
def inplace(E):
    x = E()
    x += 1
    return x

def calls():
    a = A()
    out = [a + 1, 1 + a, a == 2, a < 3, -a, a[4], A() == B(), B() == B(), B() != B(), N() != 1, a - 7, a * 8,
           attempt(lambda: a & [1, 2])]
    x = a
    x += 5
    out.append(x)
    if a == 1: out.append("test")
    out.append(log[:]); del log[:]
    e = holder("__eq__", booh)()
    out.append((holder("__eq__", booh)() == holder("__eq__", booh)(), e == e, e != e))
    for name, op in [("__lt__", lambda E: E() < E()), ("__add__", lambda E: E() + 1), ("__radd__", lambda E: 1 + E()),
                     ("__neg__", lambda E: -E()), ("__getitem__", lambda E: E()[0]), ("__iadd__", inplace),
                     ("__eq__", lambda E: E() == 1)]:
        out.append((name, attempt(lambda: op(holder(name, booh))), attempt(lambda: op(holder(name, boom)))))
    return out

expected = [("add", (1,)), ("radd", (1,)), "EQ", True, ("neg", ()), ("getitem", (4,)), "EQ", False, True, True,
            ("called", 7), ("mul", 8), 2, ("iadd", (5,)), "test",
            [("get", "add", "A", "A"), ("add", 1), ("get", "radd", "A", "A"), ("radd", 1), ("get", "eq", "A", "A"), ("eq", 1),
             ("get", "lt", "A", "A"), ("lt", 1), ("get", "neg", "A", "A"), ("neg", 0), ("get", "getitem", "A", "A"),
             ("getitem", 1), ("get", "eq", "A", "A"), ("eq", 1), "declines", "declines", "declines", "declines",
             ("get", "eq", "N", "N"), ("eq", 1), "called", ("get", "iadd", "A", "A"), ("iadd", 1),
             ("get", "eq", "A", "A"), ("eq", 1)],
            (False, True, False),
            ("__lt__", "TypeError: '<' not supported between instances of 'E' and 'E'", "KeyError: 'boom'"),
            ("__add__", "TypeError: unsupported operand type(s) for +: 'E' and 'int'", "KeyError: 'boom'"),
            ("__radd__", "TypeError: unsupported operand type(s) for +: 'int' and 'E'", "KeyError: 'boom'"),
            ("__neg__", "AttributeError: booh", "KeyError: 'boom'"),
            ("__getitem__", "AttributeError: booh", "KeyError: 'boom'"),
            ("__iadd__", "AttributeError: booh", "KeyError: 'boom'"),
            ("__eq__", False, "KeyError: 'boom'")]

def paused():
    def gen():
        a = A()
        yield a + 1
        yield a == a
        yield -a
    out = list(gen()), log[:]
    del log[:]
    return out

expected_paused = ([("add", (1,)), "EQ", ("neg", ())],
                   [("get", "add", "A", "A"), ("add", 1), ("get", "eq", "A", "A"), ("eq", 1), ("get", "neg", "A", "A"), ("neg", 0)])

def main():
    return calls(), paused()

assert_eq(main(), (expected, expected_paused))
assert_eq((calls(), paused()), (expected, expected_paused))

# A descriptor's __get__, or a property's getter, that cannot take its
# arguments raises the call's TypeError.
class NarrowGet:
    def __get__(self): return lambda: True
class NarrowBool:
    __bool__ = NarrowGet()
class PropertyBool:
    __bool__ = property(lambda: True)
class NarrowSized:
    __len__ = NarrowGet()
    __iter__ = NarrowGet()
narrow_errors = []
for make in (lambda: bool(NarrowBool()), lambda: bool(PropertyBool()), lambda: len(NarrowSized()), lambda: iter(NarrowSized()),
             lambda: [x for x in NarrowSized()]):
    try: make()
    except TypeError as e: narrow_errors.append(str(e))
narrow = "NarrowGet.__get__() takes 1 positional argument but 3 were given"
assert_eq(narrow_errors, [narrow, "PropertyBool.<lambda>() takes 0 positional arguments but 1 was given", narrow, narrow, narrow])
