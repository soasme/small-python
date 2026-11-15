# spec: PLS-315 16.6.1, 16.6.2, 16.6.3
# description: reading __annotations__ of a function, class or module the
# first time calls its __annotate__(1), the compiler's or one assigned in
# Python, and keeps the dict it returns: the compiler's evaluates each
# annotation, a Python call or a subscript of a generic class, once, in
# order, and a class's or module's only those that ran; a result that is
# not a dict is TypeError and is not kept; a starred annotation unpacks to
# its single item. Inside functions, as at module level.
from harness import *

log = []

def note(x):
    for _ in (): pass
    log.append(x)
    return x

def f(a: note("fa"), *b: note(list[int]), c: note(1) = 2) -> note("fr"): pass

class C:
    x: note("cx")
    if log is None:
        y: note("never")
    z: note(str) = 3

def bad(): pass
bad.__annotate__ = lambda fmt: [note(fmt)]

def own(): pass
own.__annotate__ = lambda fmt: {"w": note(fmt)}

def reads():
    out = [f.__annotations__, f.__annotations__ is f.__annotations__, C.__annotations__, C.__annotations__ is C.__annotations__,
           own.__annotations__, own.__annotations__ is own.__annotations__]
    for _ in range(2):
        try: bad.__annotations__
        except TypeError as e: out.append(str(e))
    class D:
        d: note(dict[str, int])
    out.append(D.__annotations__)
    return out

assert_eq(log, [])
expected = [{"a": "fa", "b": list[int], "c": 1, "return": "fr"}, True, {"x": "cx", "z": str}, True, {"w": 1}, True,
            "__annotate__() must return a dict, not list", "__annotate__() must return a dict, not list",
            {"d": dict[str, int]}]
assert_eq(reads(), expected)
assert_eq(log, ["fa", list[int], 1, "fr", "cx", str, 1, 1, 1, dict[str, int]])
log.clear()

def g(x: note(tuple[int])): pass
assert_eq(g.__annotations__, {"x": tuple[int]})
assert_eq(g.__annotate__(1), {"x": tuple[int]})
assert_raises(NotImplementedError, g.__annotate__, 3)
assert_eq(log, [tuple[int], tuple[int]])

ns = {"note": note}
exec("a: note('ma')\nif 0:\n    b: note('mb')\nc: note('mc') = 1\n", ns)
assert_eq(ns["__annotate__"](1), {"a": "ma", "c": "mc"})
assert_eq(log, [tuple[int], tuple[int], "ma", "mc"])

# A starred annotation is the single item its value unpacks to, through a
# Python __iter__ or generator; too many or too few items is ValueError.
class One:
    def __iter__(self):
        for _ in (): pass
        yield note("one")

def star(*a: *One()): pass
def star_generic[*Ts](*a: *Ts): pass
def two(*a: *[1, 2]): pass
def none(*a: *()): pass
def scalar(*a: *5): pass

assert_eq(star.__annotations__, {"a": "one"})
assert_eq(repr(star_generic.__annotations__["a"]), "typing.Unpack[Ts]")
assert_raises(ValueError, lambda: two.__annotations__)
assert_raises(ValueError, lambda: none.__annotations__)
assert_raises(TypeError, lambda: scalar.__annotations__)
assert_eq(log[-1], "one")
