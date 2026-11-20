# spec: PLS-315 24.3, 24.4.1, 7.7.8
# description: bytes.join and bytearray.join first list their iterable,
# then obtain every item's buffer in order and release them all, in the
# order obtained, once the join is done: given a list or tuple, a
# generator, an iterator, a dict, its keys or a frozenset, bound or
# unbound, inside a function as at module level. A failing item raises
# its TypeError after the buffers obtained before it are released; a
# __buffer__ that changes a listed list's size raises RuntimeError, while
# one that changes the source of an iterator or a dict leaves the listed
# items alone.
from harness import *

log = []
class E:
    def __init__(self, n, d, hook=None): self.n, self.d, self.hook = n, d, hook
    def __buffer__(self, flags):
        log.append("get" + self.n)
        if self.hook: self.hook()
        return memoryview(self.d)
    def __release_buffer__(self, view): log.append("rel" + self.n)
class Bad:
    def __buffer__(self, flags): log.append("bad"); raise ValueError("no")

def taken(f):
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    got = list(log); log.clear()
    return r, got

a, b = E("A", b"XY"), E("B", b"Q")
held = ["getA", "getB", "relA", "relB"]
assert_eq(taken(lambda: b"-".join([a, b"x", b])), (b"XY-x-Q", held))
assert_eq(taken(lambda: b"-".join((a, b))), (b"XY-Q", held))
assert_eq(taken(lambda: b"-".join(x for x in (a, b))), (b"XY-Q", held))
assert_eq(taken(lambda: b"-".join(iter([a, b]))), (b"XY-Q", held))
assert_eq(taken(lambda: b"-".join({a: 1, b: 2})), (b"XY-Q", held))
assert_eq(taken(lambda: b"-".join({a: 1, b: 2}.keys())), (b"XY-Q", held))
assert_eq(taken(lambda: b"-".join(frozenset([a]))), (b"XY", ["getA", "relA"]))
assert_eq(taken(lambda: bytes.join(b"+", (a, b))), (b"XY+Q", held))
assert_eq(taken(lambda: bytearray(b"+").join(iter((a, b)))), (bytearray(b"XY+Q"), held))
sep = b"-"
join = sep.join
assert_eq(taken(lambda: join([a, b])), (b"XY-Q", held))
def inside():
    return b"-".join([a, b]), b"=".join(x for x in [b, a])
assert_eq(taken(inside), ((b"XY-Q", b"Q=XY"), ["getA", "getB", "relA", "relB", "getB", "getA", "relB", "relA"]))

# Failures release what was obtained.
assert_eq(taken(lambda: b"-".join([a, Bad(), b])),
          (("TypeError", "sequence item 1: expected a bytes-like object, Bad found"), ["getA", "bad", "relA"]))
assert_eq(taken(lambda: b"-".join(x for x in [a, 5, b])),
          (("TypeError", "sequence item 1: expected a bytes-like object, int found"), ["getA", "relA"]))
lst = [E("C", b"c")]
lst.insert(0, E("A", b"a", lambda: lst.append(b"z")))
assert_eq(taken(lambda: b"-".join(lst)), (("RuntimeError", "sequence changed size during iteration"), ["getA", "relA"]))
src = [E("A", b"a", lambda: src.append(b"z")), b"b"]
assert_eq(taken(lambda: b"-".join(iter(src))), (b"a-b", ["getA", "relA"]))
d = {}
d[E("A", b"a", lambda: d.clear())] = 1
d[b"k"] = 2
assert_eq(taken(lambda: b"-".join(d)), (b"a-k", ["getA", "relA"]))
assert_eq(taken(lambda: b"-".join(iter([]))), (b"", []))
assert_eq(taken(lambda: b"-".join(5)), (("TypeError", "can only join an iterable"), []))
