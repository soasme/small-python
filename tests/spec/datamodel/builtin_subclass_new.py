# spec: PLS-315 10.2.3, 24.2
# description: A subclass of int, float, complex, str, bytes, tuple or
# frozenset whose __new__ is its base's builds the value the base's own
# call of the arguments gives, each Python conversion method (__int__,
# __index__, __float__, __str__, __bytes__, __buffer__, __iter__, a
# generator) running once, and holds it; its __init__ receives the
# original arguments. T.__new__(cls, ...) called by a Python __new__ or
# directly, with T itself too, type.__call__ from a metaclass's
# super().__call__, and map() build the same way. bytearray's __new__
# makes an empty array that bytearray.__init__ fills, refusing an
# exported one. Errors propagate.
from harness import *

log = []
def taken(f):
    try:
        r = f()
        r = (type(r).__name__, r)
    except Exception as e:
        r = (type(e).__name__, str(e))
    got = list(log); log.clear()
    return r, got

class X:
    def __int__(self): log.append("int"); return 5
    def __float__(self): log.append("float"); return 1.5
    def __complex__(self): log.append("complex"); return 2j
    def __bytes__(self): log.append("bytes"); return b"z"
    def __str__(self): log.append("str"); return "s"
class Idx:
    def __index__(self): log.append("index"); return 2
class Exp:
    def __buffer__(self, flags): log.append("buffer"); return memoryview(b"ex")
class It:
    def __iter__(self): log.append("iter"); return iter([3, 1])
class Raising:
    def __index__(self): log.append("index"); raise KeyError("i")
def gen():
    log.append("gen")
    yield 4
    yield 6

class I(int): pass
class F(float): pass
class C(complex): pass
class S(str): pass
class B(bytes): pass
class T(tuple): pass
class FS(frozenset): pass
class BA(bytearray): pass

assert_eq(taken(lambda: (I(X()), F(X()), C(X()), S(X()), B(X()))), (("tuple", (5, 1.5, 2j, "s", b"z")), ["int", "float", "complex", "str", "bytes"]))
assert_eq(taken(lambda: [type(v).__name__ for v in (I(Idx()), F(Idx()), C(Idx()), B(Idx()), B(Exp()), BA(Idx()), BA(Exp()))]),
          (("list", ["I", "F", "C", "B", "B", "BA", "BA"]), ["index", "index", "index", "index", "buffer", "index", "buffer"]))
assert_eq(taken(lambda: (B(Idx()), B(Exp()), BA(It()), T(It()), sorted(FS(gen())))), (("tuple", (b"\0\0", b"ex", bytearray(b"\x03\x01"), (3, 1), [4, 6])),
                                                                                     ["index", "buffer", "iter", "iter", "gen"]))
assert_eq(taken(lambda: I("11", Idx())), (("I", 3), ["index"]))
assert_eq(taken(lambda: I(Raising())), (("KeyError", "'i'"), ["index"]))
assert_eq(taken(lambda: T(Idx())), (("TypeError", "'Idx' object is not iterable"), []))
assert_eq(taken(lambda: BA(Raising())), (("KeyError", "'i'"), ["index"]))

# __init__ receives the original arguments; a bytearray subclass's own
# __init__ replaces bytearray's, so its array stays empty unless it calls it.
class Inited(tuple):
    def __init__(self, *args): log.append(("init", type(args[0]).__name__))
assert_eq(taken(lambda: Inited(It())), (("Inited", (3, 1)), ["iter", ("init", "It")]))
class Bare(bytearray):
    def __init__(self, source): log.append(("init", type(source).__name__))
assert_eq(taken(lambda: Bare(Idx())), (("Bare", bytearray()), [("init", "Idx")]))
class Filled(bytearray):
    def __init__(self, source): log.append("init"); super().__init__(source)
assert_eq(taken(lambda: Filled(Idx())), (("Filled", bytearray(2)), ["init", "index"]))

# T.__new__ called by a Python __new__ or directly; with T itself, T().
class New(int):
    def __new__(cls, v): log.append("new"); return super().__new__(cls, v)
assert_eq(taken(lambda: New(Idx())), (("New", 2), ["new", "index"]))
assert_eq(taken(lambda: (str.__new__(S, X()), tuple.__new__(T, gen()), int.__new__(int, Idx()))), (("tuple", ("s", (4, 6), 2)), ["str", "gen", "index"]))
assert_eq(taken(lambda: type(tuple.__new__(T, gen()))), (("type", T), ["gen"]))
assert_eq(taken(lambda: int.__new__(S, Idx())), (("TypeError", "int.__new__(S): S is not a subtype of int"), []))

# A metaclass's super().__call__ and map() build the same way.
class Meta(type):
    def __call__(cls, *args): log.append("meta"); return super().__call__(*args)
class MT(tuple, metaclass=Meta): pass
assert_eq(taken(lambda: MT(It())), (("MT", (3, 1)), ["meta", "iter"]))
assert_eq(taken(lambda: [type(v).__name__ for v in map(T, [It(), gen()])]), (("list", ["T", "T"]), ["iter", "gen"]))

# bytearray.__init__ empties the array and fills it; an exported one is refused.
array = BA(b"ab")
assert_eq(taken(lambda: (bytearray.__init__(array, It()), array)), (("tuple", (None, bytearray(b"\x03\x01"))), ["iter"]))
view = memoryview(array)
assert_eq(taken(lambda: array.__init__(Idx())), (("BufferError", "Existing exports of data: object cannot be re-sized"), []))
view.release()
assert_eq(taken(lambda: (array.__init__(Idx()), array)), (("tuple", (None, bytearray(2))), ["index"]))

def inside():
    return T(gen()), I(Idx()), BA(Idx()), S(X())
assert_eq(taken(inside), (("tuple", ((4, 6), 2, bytearray(2), "s")), ["gen", "index", "index", "str"]))
