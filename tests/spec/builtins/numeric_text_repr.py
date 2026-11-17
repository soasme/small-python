# spec: PLS-315 22.1.2, 22.3.1
# description: float() names text it rejects by the argument's repr, a
# str, bytes or bytearray subclass's own __repr__, which may loop, all of
# it; int() by a str subclass's, cut to 200 characters, in any base, and
# by the bytes of a bytes-like argument; a __repr__ result not a str
# raises TypeError. Text either accepts calls no __repr__, and a class with
# __float__ or __index__ converts by it. Inside functions as at module level.
from harness import *

log = []

class Looping(str):
    def __repr__(self):
        for _ in range(2): pass
        log.append("looping")
        return "L" * 250

class Plain(str):
    def __repr__(self): return "plain"

class Wrong(str):
    def __repr__(self): return 5

class Array(bytearray):
    def __repr__(self):
        for _ in (): pass
        return "array"

class Blob(bytes):
    def __repr__(self): return "blob"

class Converts(str):
    def __repr__(self): log.append("converts"); return "c"
    def __float__(self): return 2.5
    def __index__(self): return 7

class Bare(bytearray): pass

def message(f):
    try: f()
    except (ValueError, TypeError) as e: return type(e).__name__ + ": " + str(e)

def numbers():
    del log[:]
    out = [message(lambda: float(Looping("x"))), message(lambda: int(Looping("x"))), message(lambda: int(Looping("x"), 16)),
           message(lambda: int(Looping("x"), 0)), message(lambda: float(Plain("x"))), message(lambda: int(Plain("x"), 2)),
           message(lambda: float(Wrong("x"))), message(lambda: int(Wrong("x"))), message(lambda: float(Array(b"x"))),
           message(lambda: int(Array(b"x"))), message(lambda: float(Blob(b"x"))), message(lambda: int(Blob(b"x"))),
           message(lambda: float(Bare(b"x"))), message(lambda: int(Plain("x"), 1))]
    out += [float(Looping("1.5")), int(Looping("12")), int(Looping("ff"), 16), float(Array(b"2")), float(Converts("x")), int(Converts("x"))]
    return [o if not isinstance(o, str) else o.replace("L" * 250, "L*250").replace("L" * 199, "L*199") for o in out] + [log[:]]

expected = ["ValueError: could not convert string to float: L*250", "ValueError: invalid literal for int() with base 10: L*199L",
            "ValueError: invalid literal for int() with base 16: L*199L", "ValueError: invalid literal for int() with base 0: L*199L",
            "ValueError: could not convert string to float: plain", "ValueError: invalid literal for int() with base 2: plain",
            "TypeError: Wrong.__repr__() must return a str, not int", "TypeError: Wrong.__repr__() must return a str, not int",
            "ValueError: could not convert string to float: array", "ValueError: invalid literal for int() with base 10: b'x'",
            "ValueError: could not convert string to float: blob", "ValueError: invalid literal for int() with base 10: b'x'",
            "ValueError: could not convert string to float: Bare(b'x')", "ValueError: int() base must be >= 2 and <= 36, or 0",
            1.5, 12, 255, 2.0, 2.5, 7, ["looping"] * 4]

def main():
    return numbers()

assert_eq(main(), expected)
assert_eq(numbers(), expected)
