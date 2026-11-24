# spec: PLS-315 4.3, 29.5.1, 29.5.2, 29.9.1, 20.1.4, 19.3.28
# description: whether an object is an instance of a builtin class is
# decided by its type: a __class__ property naming another class is not
# read by a generic alias's or a union's comparison, a generic alias's
# arguments, a union's members, object.__reduce_ex__'s list and dict
# items, or open()'s argument checks.
from harness import *
def liar(t):
    class Liar:
        @property
        def __class__(self): return t
        def __repr__(self): return "Liar(%s)" % t.__name__
        def __iter__(self): return iter([1])
    return Liar()
GA, U = type(list[int]), type(int | str)
def checks():
    out = [list[int] == liar(GA), (int | str) == liar(U), len(GA(list, liar(tuple)).__args__),
           repr(U[int, liar(U)]), liar(list).__reduce_ex__(2)[3:], liar(dict).__reduce_ex__(2)[3:], repr(list[liar(type)])]
    for f in (lambda: open(liar(int)), lambda: open(liar(float)), lambda: open("x", liar(str)), lambda: type.__or__(int, liar(type))):
        try: out.append(f())
        except TypeError as e: out.append(str(e))
    return out
assert_eq(checks(), [False, False, 1, "int | Liar(Union)", (None, None), (None, None), "list[Liar(type)]",
                     "expected str, bytes or os.PathLike object, not Liar", "expected str, bytes or os.PathLike object, not Liar",
                     "open() argument 'mode' must be str, not Liar", NotImplemented])
