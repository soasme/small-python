# spec: PLS-315 14.3, 26.1
# description: list += y, list *= y, bytearray += y and bytearray *= y,
# y an instance, call y's reflected Python method first, since list and
# bytearray have no number slots; its result is the target's new value,
# and NotImplemented leaves the in-place operation of the list or
# bytearray itself, whose identity the target keeps. The methods may
# loop. Inside functions and generators as at module level.
from harness import *

log = []

class R:
    def __init__(self, value): self.value = value
    def __radd__(self, other):
        for _ in range(2): pass
        log.append(("radd", type(other).__name__))
        return self.value
    def __rmul__(self, other):
        for _ in range(2): pass
        log.append(("rmul", type(other).__name__))
        return self.value
    def __iter__(self): return iter([7])
    def __index__(self): return 2

def cases():
    del log[:]
    out = []
    a = [1]; a += R("sum"); out.append(a)
    a = [1]; a *= R("prod"); out.append(a)
    a = [1]; b = a; a += R(NotImplemented); out.append((a, a is b))
    a = [1]; b = a; a *= R(NotImplemented); out.append((a, a is b))
    a = bytearray(b"x"); a += R("bsum"); out.append(a)
    a = bytearray(b"x"); b = a; a *= R(NotImplemented); out.append((a, a is b))
    class D: pass
    d = D(); d.items = [1]; d.items += R("attr"); out.append(d.items)
    s = [[1]]; s[0] += R(NotImplemented); out.append(s)
    return out, log[:]

expected = (["sum", "prod", ([1, 7], True), ([1, 1], True), "bsum", (bytearray(b"xx"), True), "attr", [[1, 7]]],
            [("radd", "list"), ("rmul", "list"), ("radd", "list"), ("rmul", "list"), ("radd", "bytearray"),
             ("rmul", "bytearray"), ("radd", "list"), ("radd", "list")])

assert_eq(cases(), expected)
def gen():
    yield cases()
assert_eq(next(gen()), expected)
def main(): return cases()
assert_eq(main(), expected)
