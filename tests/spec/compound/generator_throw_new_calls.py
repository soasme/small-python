# spec: PLS-315 27.2.2, 10.2.1
# description: throw() of an exception class whose __new__ is Python code,
# which may loop, calls it with the class and the value's tuple of
# arguments, no argument for None, or the one value, then the __init__ of
# an instance of the class with the same arguments, before resuming the
# generator, also one a yield from delegates to. What the call makes that
# is not exactly of the class, without that __init__ for an exception of
# another class, is the one argument of a second call of the class, whose
# exception of any class is thrown. A result that is no exception, or an
# error from either call's __new__, is thrown into the generator in its
# place. So does an awaited athrow() of an async generator at its yield.
# Inside functions as at module level.
from harness import *

# Exceptions compare by identity, so the logs compare by repr.

log = []

class New(Exception):
    def __new__(cls, *args):
        for _ in (): pass
        log.append(("new", args))
        return super().__new__(cls, *args)
    def __init__(self, *args):
        for _ in (): pass
        log.append(("init", args))

class Other(Exception):
    def __new__(cls, *args):
        for _ in (): pass
        log.append(("other", args))
        return KeyError("other")
    def __init__(self, *args):
        log.append("not called")

class Wrapped(Exception):
    def __new__(cls, *args):
        for _ in (): pass
        if args and isinstance(args[0], KeyError): return super().__new__(cls, "wrapped", *args)
        return KeyError("inner")

class Again(Exception):
    def __new__(cls, *args):
        for _ in (): pass
        if args and isinstance(args[0], KeyError): raise LookupError("again")
        return KeyError("first")

class Base(Exception):
    def __new__(cls, *args):
        for _ in (): pass
        return super().__new__(Derived, *args)

class Derived(Base): pass

class Number(Exception):
    def __new__(cls, *args):
        for _ in (): pass
        return 5

class Boom(Exception):
    def __new__(cls, *args):
        for _ in (): pass
        raise LookupError("boom")

def gen():
    while True:
        try: yield
        except Exception as e: log.append((type(e).__name__, e.args))

def outer():
    yield from gen()

def run(g):
    next(g)
    g.throw(New); g.throw(New, 1); g.throw(New, (1, 2)); g.throw(New, None)
    g.throw(Other); g.throw(Other, "x"); g.throw(Number); g.throw(Boom)
    g.throw(Wrapped); g.throw(Again); g.throw(Base, 3); g.throw(Base, Derived(4))
    g.close()
    return log

expected = [("new", ()), ("init", ()), ("New", ()), ("new", (1,)), ("init", (1,)), ("New", (1,)),
            ("new", (1, 2)), ("init", (1, 2)), ("New", (1, 2)), ("new", ()), ("init", ()), ("New", ()),
            ("other", ()), ("other", (KeyError("other"),)), ("KeyError", ("other",)),
            ("other", ("x",)), ("other", (KeyError("other"),)), ("KeyError", ("other",)),
            ("TypeError", ("calling <class '__main__.Number'> should have returned an instance of BaseException, not int",)),
            ("LookupError", ("boom",)), ("Wrapped", (KeyError("inner"),)), ("LookupError", ("again",)),
            ("Derived", (Derived(3),)), ("Derived", (4,))]

def inside():
    return run(gen())

assert_eq(repr(inside()), repr(expected))
log.clear()
assert_eq(repr(run(outer())), repr(expected))
log.clear()
assert_eq(repr(run(gen())), repr(expected))

# A __new__ with no call or loop that returns an exception of another
# class: that instance is the argument of the class's call again.
class Other(Exception): pass
OTHER = Other("o")
class Swaps(Exception):
    def __new__(cls, *a): return a[0] if a else OTHER
def swapping():
    try: yield 1
    except BaseException as e: yield (type(e).__name__, e is OTHER)
def swapped():
    it = swapping(); next(it)
    return it.throw(Swaps)
assert_eq(swapped(), ("Other", True))
it = swapping(); next(it)
assert_eq(it.throw(Swaps), ("Other", True))

class Elsewhere(Exception):
    def __new__(cls, *args):
        for _ in (): pass
        log.append(("elsewhere", args))
        return KeyError("elsewhere")
async def async_gen():
    while True:
        try: yield 1
        except Exception as e: log.append((type(e).__name__, e.args))
async def athrows():
    a = async_gen()
    await a.asend(None)
    await a.athrow(Elsewhere)
    await a.athrow(Boom)
log.clear()
try: athrows().send(None)
except StopIteration: pass
assert_eq(repr(log), repr([("elsewhere", ()), ("elsewhere", (KeyError("elsewhere"),)), ("KeyError", ("elsewhere",)), ("LookupError", ("boom",))]))

# A class whose native __new__ gives another class's exception is called
# again with it, as raise does.
native_table = {}
class NativeElsewhere(Exception):
    __new__ = staticmethod(native_table.get)
native_table[NativeElsewhere] = KeyError("made")
def native_catching():
    while True:
        try: yield
        except Exception as e: log.append((type(e).__name__, e.args))
log.clear()
native_gen = native_catching(); next(native_gen)
native_gen.throw(NativeElsewhere)
native_gen.throw(NativeElsewhere)
native_gen.close()
assert_eq(log, [("KeyError", ("made",))] * 2)
