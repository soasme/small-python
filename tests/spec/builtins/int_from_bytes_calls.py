# spec: PLS-315 22.1.5
# description: int.from_bytes converts by a Python __bytes__, which may
# loop, once, with keywords or without, a bytes subclass result read as
# its bytes, a non-bytes result or the method's error raising, and called
# on a subclass then calls the subclass, whose Python __new__ or
# __init__ runs once, with the int.
from harness import *

log = []
class B:
    def __init__(s, v): s.v = v
    def __bytes__(s):
        for _ in (): pass
        log.append("bytes")
        if s.v == "raise": 1 / 0
        return s.v
class Plain(bytes): pass
class myint(int):
    def __new__(cls, value):
        for _ in (): pass
        log.append(("new", value))
        return int.__new__(cls, value + 1)
class myint3(int):
    def __init__(self, value):
        for _ in (): pass
        log.append("init")
        self.foo = "bar"
class Missing: pass
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
cases = [lambda: int.from_bytes(B(b"\x01\x00")), lambda: int.from_bytes(B(b"\x01\x00"), "little"),
         lambda: int.from_bytes(B(b"\xff"), signed=True), lambda: int.from_bytes(B("abc")), lambda: int.from_bytes(B("raise")),
         lambda: int.from_bytes(B(Plain(b"\x02"))), lambda: int.from_bytes(Missing()),
         lambda: (type(myint.from_bytes(b"\x01")).__name__, myint.from_bytes(B(b"\x01"), "big")),
         lambda: myint3.from_bytes(B(b"\x05")).foo, lambda: int.from_bytes([1, 2]), lambda: int.from_bytes(B(b"\x01"), "middle"),
         lambda: bool.from_bytes(B(b"\x01")), lambda: int.from_bytes(bytearray(b"\x03"))]
assert_eq([run(f) for f in cases],
          [(256, ["bytes"]), (1, ["bytes"]), (-1, ["bytes"]),
           (("TypeError", "B.__bytes__() must return a bytes, not str"), ["bytes"]),
           (("ZeroDivisionError", "division by zero"), ["bytes"]), (2, ["bytes"]),
           (("TypeError", "cannot convert 'Missing' object to bytes"), []),
           (("myint", 2), [("new", 1), "bytes", ("new", 1)]), ("bar", ["bytes", "init"]), (258, []),
           (("ValueError", "byteorder must be either 'little' or 'big'"), []), (True, ["bytes"]), (3, [])])
def inner():
    for _ in (): pass
    return int.from_bytes(B(b"\x07")) + myint.from_bytes(B(b"\x01"))
assert_eq(run(inner), (9, ["bytes", "bytes", ("new", 1)]))
