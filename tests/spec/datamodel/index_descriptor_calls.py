# spec: PLS-315 7.5.3, 7.5.4, 7.3.2
# description: An __index__ that the class holds as a descriptor, a
# Python __get__ or a property's getter, is read once per conversion,
# then what the read returns is called: for subscription, slicing, a
# sequence's repetition, item and slice stores and deletions of lists,
# bytearrays and memoryviews, and builtins taking an index. Checking that
# the type defines __index__ reads nothing. A read's error propagates; the
# read may loop and pause in a generator. Inside functions as at module
# level.
from harness import *

log = []
class Reads:
    def __get__(self, obj, owner):
        for _ in range(2): pass
        log.append("get")
        def index():
            for _ in range(2): pass
            log.append("call")
            return obj.v
        return index
class I:
    __index__ = Reads()
    def __init__(self, v): self.v = v
class P:
    def __init__(self, v): self.v = v
    @property
    def __index__(self):
        for _ in range(2): pass
        log.append("prop")
        return lambda: self.v
class Fails:
    @property
    def __index__(self):
        raise LookupError("read")

def counted(f):
    del log[:]
    try: r = f()
    except Exception as e: r = type(e).__name__ + ": " + str(e)
    return r, log.count("get"), log.count("call"), log.count("prop")

def stores():
    l = list(range(6))
    l[I(1)] = "x"
    del l[I(0)]
    l[I(0):I(2)] = "ab"
    b = bytearray(b"abc")
    b[I(1)] = 65
    del b[I(0)]
    v = memoryview(bytearray(b"xyz"))
    v[I(0)] = 66
    return l, b, v.tobytes()

def calls():
    l = list(range(10))
    return [counted(lambda: l[I(3)]), counted(lambda: l[I(1):I(4)]), counted(lambda: l[::I(2)]),
            counted(lambda: "ab" * I(2)), counted(lambda: [0] * I(3)), counted(lambda: (1, 2, 3)[I(-1)]),
            counted(lambda: l[P(5)]), counted(lambda: l[Fails()]), counted(stores),
            counted(lambda: bytearray(I(3))), counted(lambda: list(range(I(3)))), counted(lambda: "abcb".index("b", I(2))),
            counted(lambda: [1, 2, 3].pop(I(0))), counted(lambda: bytes(I(2)))]

expected = [(3, 1, 1, 0), ([1, 2, 3], 2, 2, 0), ([0, 2, 4, 6, 8], 1, 1, 0), ("abab", 1, 1, 0), ([0, 0, 0], 1, 1, 0),
            (3, 1, 1, 0), (5, 0, 0, 1), ("LookupError: read", 0, 0, 0),
            ((["a", "b", 3, 4, 5], bytearray(b"Ac"), b"Byz"), 7, 7, 0),
            (bytearray(b"\x00\x00\x00"), 1, 1, 0), ([0, 1, 2], 1, 1, 0), (3, 1, 1, 0), (1, 1, 1, 0), (b"\x00\x00", 1, 1, 0)]

def paused():
    def gen():
        l = [5, 6, 7]
        yield l[I(1)]
        yield l[I(0):I(2)]
    del log[:]
    return list(gen()), log.count("get")

def main():
    return calls(), paused()

assert_eq(main(), (expected, ([6, [5, 6]], 3)))
assert_eq((calls(), paused()), (expected, ([6, [5, 6]], 3)))
