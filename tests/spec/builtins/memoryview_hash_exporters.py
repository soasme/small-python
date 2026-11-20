# spec: PLS-315 24.4.2
# description: hash() of a read-only memoryview, its own __hash__ bound or
# unbound, and a dict lookup of it, hash its exporter first, by the
# exporter's Python __hash__, then hash the view's bytes and keep that
# hash, so a second hash calls no Python. An exporter's error or a
# non-int hash propagates; the view stays exported while the exporter
# hashes, so releasing it there raises BufferError.
from harness import *

log = []
class E(bytes):
    def __hash__(self): log.append("hash"); return 7
class Bad(bytes):
    def __hash__(self): log.append("bad"); raise KeyError("h")
class NotInt(bytes):
    def __hash__(self): log.append("str"); return "x"

def taken(f):
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    got = list(log); log.clear()
    return r, got

m = memoryview(E(b"abc"))
assert_eq(taken(lambda: hash(m) == hash(b"abc")), (True, ["hash"]))
assert_eq(taken(lambda: hash(m) == hash(b"abc")), (True, []))
assert_eq(taken(lambda: hash(memoryview(E(b"abc"))) == hash(b"abc")), (True, ["hash"]))
assert_eq(taken(lambda: memoryview(E(b"q")).__hash__() == hash(b"q")), (True, ["hash"]))
assert_eq(taken(lambda: memoryview.__hash__(memoryview(E(b"q"))) == hash(b"q")), (True, ["hash"]))
assert_eq(taken(lambda: {}.get(memoryview(E(b"q")), 5)), (5, ["hash"]))
assert_eq(taken(lambda: hash(memoryview(Bad(b"x")))), (("KeyError", "'h'"), ["bad"]))
assert_eq(taken(lambda: hash(memoryview(NotInt(b"x")))), (("TypeError", "__hash__ method should return an integer"), ["str"]))
assert_eq(taken(lambda: hash(memoryview(bytearray(E(b"x"))))), (("ValueError", "cannot hash writable memoryview object"), []))
def inside():
    v = memoryview(E(b"zz"))
    return hash(v) == hash(b"zz"), v.__hash__() == hash(b"zz")
assert_eq(taken(inside), ((True, True), ["hash"]))

class Releasing(bytes):
    def __hash__(self):
        try: view.release()
        except BufferError as e: log.append(type(e).__name__)
        return 1
view = memoryview(Releasing(b"r"))
assert_eq(taken(lambda: hash(view) == hash(b"r")), (True, ["BufferError"]))
view.release()
assert_eq(hash(view), hash(b"r"))
