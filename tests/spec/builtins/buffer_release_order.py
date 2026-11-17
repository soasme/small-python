# spec: PLS-315 24.4.1
# description: an operation reading the buffers of several exporters whose
# Python __buffer__ and __release_buffer__ loop obtains each as it reads
# it and releases them all, in the order obtained, once it finishes:
# bytes.replace, bytes.join and bytearray.join of a list or tuple, and
# find() and in; startswith() and endswith() given a tuple obtain and
# release each choice in turn and stop at the first match, bound or
# unbound, of a bytearray or a subclass, with bounds or through f(*args);
# a memoryview compared with an exporter releases its buffer. A join reads each item
# once, when it reaches it: an exporter that empties the list makes it
# raise RuntimeError, one that replaces itself or a later item is read as
# it was or as it now is. Inside functions as at module level.
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

class Bs(bytes): pass

def star(f, *args):
    for _ in (): pass
    return f(*args)

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
            logged(lambda: memoryview(b"XY") == x),
            logged(lambda: bytes.startswith(b"XYz", (y, x))),
            logged(lambda: bytes.endswith(b"zXY", (y, x), 1)),
            logged(lambda: bytearray(b"XYz").startswith((y, x))),
            logged(lambda: Bs(b"zXY").endswith((y, x), 1)),
            logged(lambda: star(b"XYz".startswith, (y, x))),
            logged(lambda: star(b"-".join, [x, y])),
            logged(lambda: b"XYz".startswith((y, y)))]

expected = [(b"zQz", ["getX", "getY", "relX", "relY"]),
            (b"XY-Q", ["getX", "getY", "relX", "relY"]),
            (bytearray(b"Q-XY"), ["getY", "getX", "relY", "relX"]),
            (1, ["getX", "relX"]),
            (True, ["getX", "relX"]),
            (True, ["getX", "relX"]),
            (True, ["getY", "relY", "getX", "relX"]),
            (True, ["getY", "relY"]),
            (True, ["getX", "relX"]),
            (True, ["getY", "relY", "getX", "relX"]),
            (True, ["getY", "relY", "getX", "relX"]),
            (True, ["getY", "relY", "getX", "relX"]),
            (True, ["getY", "relY", "getX", "relX"]),
            (True, ["getY", "relY", "getX", "relX"]),
            (b"XY-Q", ["getX", "getY", "relX", "relY"]),
            (False, ["getY", "relY", "getY", "relY"])]

class Mutating:
    def __init__(self, mutate): self.mutate = mutate
    def __buffer__(self, flags):
        for _ in range(2): pass
        self.mutate()
        return memoryview(b"x")

def mutations():
    out = []
    for sep in (b"-", bytearray(b"-")):
        seq = [b"a", Mutating(lambda: seq.clear()), b"c"]
        out.append(str(assert_raises(RuntimeError, sep.join, seq)))
        def replace(): seq[1] = b"z"
        seq = [b"a", Mutating(replace), b"c"]
        out.append(sep.join(seq))
        def later(): seq[2] = b"q"
        seq = [b"a", Mutating(later), b"c"]
        out.append(sep.join(seq))
    return out

changed = ["sequence changed size during iteration", b"a-x-c", b"a-x-q"] * 2

def main():
    assert_eq(mutations(), changed)
    return orders()

assert_eq(main(), expected)
assert_eq(orders(), expected)
assert_eq(mutations(), changed)
