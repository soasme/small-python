# spec: PLS-315 24.3, 24.4.1
# description: `in` and `not in` of a bytes or bytearray try the operand's
# __index__ first; when it raises or returns a non-int, the error is
# discarded and the operand's __buffer__ gives the needle, its buffer
# released after the search; a __buffer__ that raises propagates. The
# result feeds a test, a chained comparison and a comprehension's filter
# alike, and a bytearray stays exported until the search ends.
from harness import *

log = []
class N:
    def __init__(self, ix, d): self.ix, self.d = ix, d
    def __index__(self):
        log.append("index")
        if self.ix == "raise": raise ValueError("ix")
        if self.ix == "str": return "x"
        return self.ix
    def __buffer__(self, flags):
        log.append("get")
        if self.d is None: raise KeyError("buf")
        return memoryview(self.d)
    def __release_buffer__(self, view): log.append("rel")

def taken(f):
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    got = list(log); log.clear()
    return r, got

searched = ["index", "get", "rel"]
assert_eq(taken(lambda: N("raise", b"bc") in b"abcd"), (True, searched))
assert_eq(taken(lambda: N("str", b"bc") not in b"abcd"), (False, searched))
assert_eq(taken(lambda: N("raise", b"zz") in bytearray(b"abcd")), (False, searched))
assert_eq(taken(lambda: N("raise", None) in b"abcd"), (("KeyError", "'buf'"), ["index", "get"]))
assert_eq(taken(lambda: N(98, b"zz") in b"abcd"), (True, ["index"]))
assert_eq(taken(lambda: 1 if N("raise", b"a") in b"abc" else 2), (1, searched))
assert_eq(taken(lambda: N("raise", b"a") in b"abc" in [True]), (False, searched))
assert_eq(taken(lambda: len([x for x in [N("raise", b"a")] if x in b"abc"])), (1, searched))
def inside():
    return N("raise", b"cd") in b"abcd", N("raise", b"x") not in bytearray(b"abcd")
assert_eq(taken(inside), ((True, True), searched + searched))

class Clearing:
    def __init__(self, a): self.a = a
    def __index__(self): raise ValueError
    def __buffer__(self, flags):
        log.append("get")
        try: self.a.clear()
        except BufferError as e: log.append(str(e))
        return memoryview(b"A")
a = bytearray(b"A")
assert_eq(taken(lambda: Clearing(a) in a), (True, ["get", "Existing exports of data: object cannot be re-sized"]))
assert_eq(a, bytearray(b"A"))
a.clear()
assert_eq(a, bytearray())
