# spec: PLS-315 24.4.2
# description: a view's obj is the bytes, bytearray or subclass instance
# it views, and every view derived from it by memoryview, slicing,
# toreadonly or cast has the same obj; a view a Python __buffer__ returned
# has some obj, the same for the views derived from it. Inside functions as
# at module level.
from harness import *

class BA(bytearray): pass
class BB(bytes): pass

class Exporter:
    def __init__(self): self.data = bytearray(b"ab")
    def __buffer__(self, flags):
        for _ in (): pass
        return memoryview(self.data)

def owners():
    out = []
    for o in (b"ab", bytearray(b"ab"), BA(b"ab"), BB(b"ab")):
        m = memoryview(o)
        out.append([v.obj is o for v in (m, memoryview(m), m[1:], m.toreadonly(), m.cast("b"))])
    v = memoryview(Exporter())
    out.append([w.obj is v.obj for w in (memoryview(v), v[1:], v.toreadonly(), v.cast("b"))])
    return out

expected = [[True] * 5] * 4 + [[True] * 4]

def main():
    return owners()

assert_eq(main(), expected)
assert_eq(owners(), expected)
