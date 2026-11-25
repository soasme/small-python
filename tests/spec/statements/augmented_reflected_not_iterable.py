# spec: PLS-315 7.6.3, 7.7.1, 14.3
# description: once y's reflected __radd__ declines with NotImplemented,
# list += y appends y's items, raising GetIterator's TypeError when y is
# not iterable, its __iter__ None included, and leaving the list unchanged;
# bytearray += y raises "can't concat" for any y that is not bytes-like.
from harness import assert_eq

class P:
    def __radd__(self, other):
        for _ in (): pass
        return NotImplemented

class Blocked(P):
    __iter__ = None

class Items(P):
    def __iter__(self): return iter([7, 8])

def concat(x, y):
    try:
        x += y
    except TypeError as e:
        return str(e)
    return x

def run():
    out = []
    for y in (P(), Blocked(), Items()):
        a = [1]
        out.append((concat(a, y), a))
    return out

assert_eq(run(), [("'P' object is not iterable", [1]), ("'Blocked' object is not iterable", [1]),
                  ([1, 7, 8], [1, 7, 8])])
b = bytearray(b"a")
assert_eq([concat(b, y) for y in (P(), Items())], ["can't concat P to bytearray", "can't concat Items to bytearray"])
assert_eq(b, bytearray(b"a"))
