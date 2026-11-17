# spec: PLS-315 24.4.1
# description: an operation reading the buffers of several exporters whose
# Python __buffer__ and __release_buffer__ loop obtains each as it reads
# it and releases them all, in the order obtained, once it finishes:
# bytes.replace, bytes.join and bytearray.join of a list or tuple, and
# find() and in; startswith() and endswith() given a tuple obtain and
# release each choice in turn and stop at the first match; a memoryview
# compared with an exporter releases its buffer. Inside functions as at
# module level.
from harness import *

log = []

class Exporter:
    def __init__(self, name, data): self.name = name; self.data = data
    def __buffer__(self, flags):
        for _ in range(2): pass
        log.append("get" + self.name)
        return memoryview(self.data)
    def __release_buffer__(self, view):
        for _ in range(2): pass
        log.append("rel" + self.name)

x, y = Exporter("X", b"XY"), Exporter("Y", b"Q")

def logged(call):
    del log[:]
    return call(), list(log)

def orders():
    return [logged(lambda: b"zXYz".replace(x, y)),
            logged(lambda: b"-".join([x, y])),
            logged(lambda: bytearray(b"-").join((y, x))),
            logged(lambda: b"aXY".find(x)),
            logged(lambda: x in b"aXY"),
            logged(lambda: b"XYz".startswith((x, y))),
            logged(lambda: b"XYz".startswith((y, x))),
            logged(lambda: b"zXY".endswith((y, b"Y"))),
            logged(lambda: memoryview(b"XY") == x)]

expected = [(b"zQz", ["getX", "getY", "relX", "relY"]),
            (b"XY-Q", ["getX", "getY", "relX", "relY"]),
            (bytearray(b"Q-XY"), ["getY", "getX", "relY", "relX"]),
            (1, ["getX", "relX"]),
            (True, ["getX", "relX"]),
            (True, ["getX", "relX"]),
            (True, ["getY", "relY", "getX", "relX"]),
            (True, ["getY", "relY"]),
            (True, ["getX", "relX"])]

def main():
    return orders()

assert_eq(main(), expected)
assert_eq(orders(), expected)
