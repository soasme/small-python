# spec: PLS-315 24.2, 24.3, 23.6
# description: bytearray % of instances calls their Python methods, each
# of which may loop, in the specs' order, as bytes % does, and returns a
# bytearray; the receiver stays exported until the formatting ends, so a
# method resizing it raises BufferError while a same-length write is
# allowed, and an exception from a method propagates with the export
# released. Inside functions, generators and comprehensions as at module
# level.
from harness import *

log = []

class N:
    def __init__(self, v): self.v = v
    def __index__(self):
        for _ in (): pass
        log.append(("index", self.v))
        if self.v is None: raise LookupError("index")
        return self.v
    def __int__(self):
        for _ in (): pass
        log.append(("int", self.v)); return self.v
    def __float__(self):
        for _ in (): pass
        log.append(("float", self.v)); return 0.5
    def __repr__(self):
        for _ in (): pass
        log.append(("repr", self.v)); return "Né"
    def __bytes__(self):
        for _ in (): pass
        log.append(("bytes", self.v)); return b"by"

def run():
    t = bytearray(b"%d|%x|%c|%.1f|%r|%a|%s|%b") % (N(7), N(255), N(66), N(0), N(1), N(2), N(3), N(4))
    m = bytearray(b"%(k)s-%(j)x") % {b"k": N(5), b"j": N(10)}
    return t, m, type(t).__name__

expected = (bytearray(b"7|ff|B|0.5|N\\xe9|N\\xe9|by|by"), bytearray(b"by-a"), "bytearray")
expected_log = [("int", 7), ("index", 255), ("index", 66), ("float", 0), ("repr", 1), ("repr", 2),
                ("bytes", 3), ("bytes", 4), ("bytes", 5), ("index", 10)]
assert_eq(run(), expected)
assert_eq(log, expected_log)
log.clear()

t = bytearray(b"%d|%x|%c|%.1f|%r|%a|%s|%b") % (N(7), N(255), N(66), N(0), N(1), N(2), N(3), N(4))
assert_eq(t, expected[0])
assert_eq(log, expected_log[:8])
log.clear()

def gen():
    yield bytearray(b"%x") % N(11)
    yield [bytearray(b"%c") % N(v) for v in (67, 68)]

assert_eq(list(gen()), [bytearray(b"b"), [bytearray(b"C"), bytearray(b"D")]])
assert_eq(log, [("index", 11), ("index", 67), ("index", 68)])
log.clear()

# The receiver is exported while the methods run.
class Grow:
    def __init__(self, target): self.target = target
    def __index__(self):
        for _ in (): pass
        try: self.target.append(0)
        except BufferError as e: log.append(str(e))
        self.target[0] = ord("%")
        return 69

def exported():
    b = bytearray(b"#c%c")
    out = b % Grow(b)
    b.append(1)
    return out, b

assert_eq(exported(), (bytearray(b"#cE"), bytearray(b"%c%c\x01")))
assert_eq(log, ["Existing exports of data: object cannot be re-sized"])
log.clear()

def errors():
    b = bytearray(b"%x %x")
    try: b % (N(1), N(None))
    except LookupError as e: log.append(e.args)
    b.append(2)
    return b

assert_eq(errors(), bytearray(b"%x %x\x02"))
assert_eq(log, [("index", 1), ("index", None), ("index",)])
