# spec: PLS-315 24.4.1, 24.4.2
# description: memoryview() of an instance whose class has a Python
# __buffer__ and no bytes or bytearray base calls it with the flags
# PyBUF_FULL_RO, 284, its result's buffer viewed, written through to the
# exporter's storage; the method may loop, its exception propagates, and
# a result that is no memoryview raises TypeError naming the class.
# Inside functions as at module level.
from harness import *

log = []

class Exporter:
    def __init__(self, data): self.data = bytearray(data)
    def __buffer__(self, flags):
        for _ in range(2): pass
        log.append(("buffer", flags))
        if self.data == b"bad": raise ValueError("bad")
        if self.data == b"str": return "text"
        return memoryview(self.data)

def failure(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def views():
    del log[:]
    e = Exporter(b"abc")
    m = memoryview(e)
    out = [bytes(m), m.readonly, m.nbytes, m.format]
    m[0] = ord("x")
    out += [bytes(e.data), failure(lambda: memoryview(Exporter(b"bad"))), failure(lambda: memoryview(Exporter(b"str")))]
    return out + [list(log)]

expected = [b"abc", False, 3, "B", b"xbc", ("ValueError", "bad"), ("TypeError", "Exporter.__buffer__() must return a memoryview, not str"),
            [("buffer", 284), ("buffer", 284), ("buffer", 284)]]

def main():
    return views()

assert_eq(main(), expected)
assert_eq(views(), expected)
