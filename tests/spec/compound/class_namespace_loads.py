# spec: PLS-315 9.3.1, 9.3.3, 16.4.2
# description: a class body loads each name through the Python __getitem__
# of the namespace __prepare__ returned, which may loop: in expressions,
# arithmetic, calls and their callees, an augmented assignment's target, a
# for loop's iterable, a comprehension's first iterable, defaults,
# decorators and a nested class's bases; on a KeyError a local name falls
# back to the globals and builtins and a free name to its cell; another
# exception propagates, and a missing name raises NameError; a name
# declared global skips the namespace. Inside functions as at module level.
from harness import *

log = []

class Namespace(dict):
    def __getitem__(self, key):
        for _ in (): pass
        log.append(key)
        if key == "boom": raise LookupError("boom")
        return dict.__getitem__(self, key)

class Meta(type):
    @classmethod
    def __prepare__(meta, name, bases): return Namespace()

g = 10
boom = "global boom"

def decorate(f):
    log.append("decorate")
    return f

def outer():
    free = 5
    class C(metaclass=Meta):
        a = 1
        b = a + g
        c = [a, len("xy")]
        d = free
        a += 2
        for i in range(2): pass
        def f(self, x=a): return x
        f = decorate(f)
        lam = lambda y=b: y
        e = [z for z in c]
        class D(int): pass
        try: missing
        except NameError as ex: err = str(ex)
    return C

C = outer()
assert_eq((C.a, C.b, C.c, C.d, C.f(C()), C.lam(), C.e, C.err),
          (3, 11, [1, 2], 5, 3, 11, [1, 2], "name 'missing' is not defined"))
assert_eq(log, ["__name__", "a", "g", "a", "len", "free", "a", "range", "a", "decorate", "f",
                "decorate", "b", "c", "int", "missing", "NameError", "str", "ex"])
log.clear()

# A __getitem__ error other than KeyError propagates; a global name skips it.
def errors():
    out = []
    try:
        class E(metaclass=Meta):
            x = boom
    except LookupError as e: out.append(e.args)
    class F(metaclass=Meta):
        global boom
        y = boom
    out.append(F.y)
    return out

assert_eq(errors(), [("boom",), "global boom"])
assert_eq(log, ["__name__", "boom", "__name__"])
log.clear()

class G(metaclass=Meta):
    h = g * 2
    k = [x for x in range(h // 10)]
assert_eq((G.h, G.k), (20, [0, 1]))
assert_eq(log, ["__name__", "g", "range", "h"])
