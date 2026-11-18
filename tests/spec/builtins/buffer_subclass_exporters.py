# spec: PLS-315 24.4.1
# description: a bytes or bytearray subclass whose class defines __buffer__
# exports its buffer by that method: memoryview(), bytearray(), join, +,
# in, find's, count's and replace's argument, int.from_bytes and bytearray's +=
# call it, and a bytearray's comparisons and decode call it on both
# operands and on itself, as do bytes(), str(o, encoding) and the argument
# of startswith and endswith of a bytearray subclass; bytes() of a bytes
# subclass, a bytes comparison, decode and str(o, encoding) of one,
# startswith's and endswith's argument, and the receiver of other methods
# read its contents. One object a join reads twice is asked twice, and
# int.from_bytes asks for a buffer before __bytes__; so do bytes.__add__,
# bytearray.__add__ and bytearray's comparison methods called directly. Inside functions as
# at module level.
from harness import *

log = []

class B(bytes):
    def __buffer__(self, flags):
        for _ in (): pass
        log.append("getB")
        return memoryview(b"BUF")
    def __release_buffer__(self, view):
        for _ in (): pass
        log.append("relB")

class A(bytearray):
    def __buffer__(self, flags):
        for _ in (): pass
        log.append("getA")
        return memoryview(b"BUF")
    def __release_buffer__(self, view):
        for _ in (): pass
        log.append("relA")

class E:
    def __buffer__(self, flags):
        for _ in (): pass
        log.append("getE")
        return memoryview(b"E")

class P:
    def __bytes__(self):
        for _ in (): pass
        log.append("bytes")
        return b"BY"
    def __buffer__(self, flags):
        for _ in (): pass
        log.append("buf")
        return memoryview(b"BU")

def logged(call):
    del log[:]
    result = call()
    if isinstance(result, memoryview):
        result = bytes(result)
    return result, list(log)

def consumers(x):
    head, tail, both = b"a", b"xownx", b"own"
    return [logged(lambda: memoryview(x)), logged(lambda: bytes(x)), logged(lambda: bytearray(x)),
            logged(lambda: head + x), logged(lambda: x + head), logged(lambda: both == x),
            logged(lambda: x == both), logged(lambda: x in tail), logged(lambda: tail.find(x)),
            logged(lambda: x.find(b"w")), logged(lambda: both.replace(x, b"Z")), logged(lambda: x.decode()),
            logged(lambda: str(x, "ascii")), logged(lambda: int.from_bytes(x, "big")),
            logged(lambda: tail.startswith(x)), logged(lambda: x.startswith(b"o")),
            logged(lambda: tail.count(x)), logged(lambda: tail.endswith(x)), logged(lambda: x.upper())]

def grow(x):
    a = bytearray(b"-")
    a += x
    return a

def others(e):
    return [logged(lambda: b"-".join([e, e])), logged(lambda: b"-".join([e, b"x", e])),
            logged(lambda: bytearray(b"E") == e), logged(lambda: e == bytearray(b"E")),
            logged(lambda: bytearray(b"a") < memoryview(b"b")), logged(lambda: int.from_bytes(P(), "big")),
            logged(lambda: grow(B(b"own"))), logged(lambda: grow(A(b"own"))),
            logged(lambda: bytes.__add__(b"a", B(b"own"))), logged(lambda: bytearray.__add__(bytearray(b"a"), e)),
            logged(lambda: bytearray.__eq__(bytearray(b"E"), e)), logged(lambda: bytearray.__lt__(A(b"own"), b"z"))]

get, rel = ["getB", "relB"], ["getA", "relA"]
expected_b = [(b"BUF", get), (b"own", []), (bytearray(b"BUF"), get), (b"aBUF", get), (b"BUFa", get),
              (True, []), (True, []), (False, get), (-1, get), (1, []), (b"own", get), ("own", []), ("own", []),
              (4347206, get), (False, []), (True, []), (0, get), (False, []), (b"OWN", [])]
expected_a = [(b"BUF", rel), (b"BUF", rel), (bytearray(b"BUF"), rel), (b"aBUF", rel), (bytearray(b"BUFa"), rel),
              (False, rel), (False, rel), (False, rel), (-1, rel), (1, []), (b"own", rel), ("BUF", rel), ("BUF", rel),
              (4347206, rel), (False, rel), (True, []), (0, rel), (False, rel), (bytearray(b"OWN"), [])]
expected_others = [(b"E-E", ["getE", "getE"]), (b"E-x-E", ["getE", "getE"]), (True, ["getE"]), (True, ["getE"]),
                   (True, []), (16981, ["buf"]), (bytearray(b"-BUF"), get), (bytearray(b"-BUF"), rel),
                   (b"aBUF", get), (bytearray(b"aE"), ["getE"]), (True, ["getE"]), (True, rel)]

def main():
    return consumers(B(b"own")), consumers(A(b"own")), others(E())

assert_eq(main(), (expected_b, expected_a, expected_others))
assert_eq((consumers(B(b"own")), consumers(A(b"own")), others(E())), (expected_b, expected_a, expected_others))
