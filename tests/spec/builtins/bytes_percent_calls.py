# spec: PLS-315 24.3, 23.6
# description: bytes % of instances calls their Python methods, each of
# which may loop, in the specs' order: __int__ for %d, __index__ for %x
# and %c, __float__ for %f, __repr__ for %r and %a, its text escaped to
# ASCII, and __bytes__ for %s and %b, also through a mapping key; a bytes
# subclass's own bytes are taken without its __bytes__. A __bytes__
# returning other than bytes is a TypeError; a str's %c takes a TypeError
# of __index__ as its own, a bytes's raises it. Inside functions as at
# module level.
from harness import *

log = []

class N:
    def __init__(self, v): self.v = v
    def __index__(self):
        for _ in (): pass
        log.append("index")
        if self.v is None: raise TypeError("index")
        return self.v
    def __int__(self):
        for _ in (): pass
        log.append("int"); return self.v
    def __float__(self):
        for _ in (): pass
        log.append("float"); return 0.5
    def __repr__(self):
        for _ in (): pass
        log.append("repr"); return "Né"
    def __bytes__(self):
        for _ in (): pass
        log.append("bytes")
        return b"nb" if self.v else 5

class Own(bytes):
    def __bytes__(self):
        for _ in (): pass
        log.append("own"); return b"no"

def run():
    for _ in (): pass
    return [b"%d|%x|%c" % (N(5), N(255), N(65)), b"%f" % N(1), b"%r %a" % (N(1), N(2)), b"%s%b" % (N(3), N(3)),
            b"%(k)d %(k)c" % {b"k": N(66)}, b"%s" % Own(b"yes")]

expected = [b"5|ff|A", b"0.500000", b"N\\xe9 N\\xe9", b"nbnb", b"66 B", b"yes"]
expected_log = ["int", "index", "index", "float", "repr", "repr", "bytes", "bytes", "int", "index"]
assert_eq(run(), expected)
assert_eq(log, expected_log)
log.clear()

assert_eq([b"%d|%x|%c" % (N(5), N(255), N(65)), b"%s" % Own(b"yes")], [expected[0], expected[5]])
assert_eq(log, expected_log[:3])
log.clear()

def errors_here():
    out = []
    for f in (lambda: b"%s" % N(0), lambda: "%c" % N(None), lambda: b"%c" % N(None)):
        try: f()
        except TypeError as e: out.append(str(e))
    try:
        for _ in (): pass
        b"%c" % N(300)
    except OverflowError as e: out.append(str(e))
    try:
        for _ in (): pass
        "%c" % (N("s"),)
    except TypeError as e: out.append(str(e))
    return out

assert_eq(errors_here(), ["N.__bytes__() must return a bytes, not int",
                          "format argument: %c requires an integer or a unicode character, not N", "index",
                          "format argument: %c argument not in range(256)",
                          "format argument 1: %c requires an integer or a unicode character, not N"])
