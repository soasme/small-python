# spec: PLS-315 24.3, 24.4.2
# description: bytes.hex, bytearray.hex and memoryview.hex convert
# bytes_per_sep first, then take the separator's length by its Python
# __len__, then its type: a length other than 1 raises ValueError, a
# separator neither str nor bytes TypeError, and the first character
# separates. Positional or keyword, bound or unbound. The receiver stays
# exported while __len__ runs, so resizing the bytearray or releasing the
# view there raises BufferError.
from harness import *

log = []
class T(str):
    def __len__(self): log.append("len"); return 1
class G:
    def __index__(self): log.append("index"); return 2
class Two(bytes):
    def __len__(self): log.append("len"); return 2
class Neg(bytes):
    def __len__(self): log.append("len"); return -1
class Raise(bytes):
    def __len__(self): log.append("len"); raise KeyError("l")
class Long(bytes):
    def __len__(self): return 1
class Listed(list):
    def __len__(self): log.append("len"); return 1

def taken(f):
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    got = list(log); log.clear()
    return r, got

assert_eq(taken(lambda: b"abcd".hex(T(":"))), ("61:62:63:64", ["len"]))
assert_eq(taken(lambda: b"abcd".hex(T(":"), G())), ("6162:6364", ["index", "len"]))
assert_eq(taken(lambda: bytes.hex(b"abcd", T(":"), 2)), ("6162:6364", ["len"]))
assert_eq(taken(lambda: bytearray.hex(bytearray(b"abcd"), T(":"), G())), ("6162:6364", ["index", "len"]))
assert_eq(taken(lambda: memoryview(b"abcd").hex(T("."))), ("61.62.63.64", ["len"]))
assert_eq(taken(lambda: memoryview(b"abcd").hex(":", bytes_per_sep=G())), ("6162:6364", ["index"]))
assert_eq(taken(lambda: b"abcd".hex(sep=T(":"))), ("61:62:63:64", ["len"]))
assert_eq(taken(lambda: b"abcd".hex(T(":"), bytes_per_sep=G())), ("6162:6364", ["index", "len"]))
assert_eq(taken(lambda: b"ab".hex(Long(b"=+"))), ("61=62", []))
assert_eq(taken(lambda: b"ab".hex(Two(b":"))), (("ValueError", "sep must be length 1."), ["len"]))
assert_eq(taken(lambda: b"ab".hex(Neg(b":"))), (("ValueError", "__len__() should return >= 0"), ["len"]))
assert_eq(taken(lambda: b"ab".hex(Raise(b":"))), (("KeyError", "'l'"), ["len"]))
assert_eq(taken(lambda: b"ab".hex(Listed([1]))), (("TypeError", "sep must be str or bytes."), ["len"]))
hexed = b"abcd".hex
def inside(): return hexed(T("-"), G()), memoryview(b"xy").hex(T("/"))
assert_eq(taken(inside), (("6162-6364", "78/79"), ["index", "len", "len"]))

ba = bytearray(b"abc")
class Clearing(bytes):
    def __len__(self): ba.clear(); return 1
assert_eq(taken(lambda: ba.hex(Clearing(b":"))), (("BufferError", "Existing exports of data: object cannot be re-sized"), []))
assert_eq(ba, bytearray(b"abc"))
mv = memoryview(bytearray(b"xyz"))
class Releasing(bytes):
    def __len__(self): mv.release(); return 1
assert_eq(taken(lambda: mv.hex(Releasing(b":"))), (("BufferError", "memoryview has 1 exported buffer"), []))
assert_eq(mv.hex(), "78797a")
