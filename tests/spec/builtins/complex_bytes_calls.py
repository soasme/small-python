# spec: PLS-315 22.4.1, 24.1.1, 10.5
# description: complex() and bytes() of an instance call its class's
# __complex__ or __bytes__, which may loop, inside functions as at module
# level: a complex subclass's result becomes an exact complex, a bytes
# subclass's is returned as it is, and any other result raises TypeError
# naming the method; the method's exceptions propagate. complex() with an
# imaginary part adds it to the converted real part.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Exact(complex): pass
class Data(bytes): pass

class Number:
    def __init__(self, value): self.value = value
    def __complex__(self):
        spin()
        log.append(("complex", self.value))
        if self.value == "bad":
            raise ValueError("complex")
        return self.value

class Blob:
    def __init__(self, value): self.value = value
    def __bytes__(self):
        spin()
        log.append(("bytes", self.value))
        if self.value == "bad":
            raise KeyError("bytes")
        return self.value

def error(f):
    try:
        r = f()
        return type(r).__name__, r
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    out = [error(lambda: complex(Number(1j))), error(lambda: complex(Number(Exact(2j)))), error(lambda: complex(Number(1.5))),
           error(lambda: complex(Number("bad"))), error(lambda: complex(Number(1j), 1)),
           error(lambda: bytes(Blob(b"x"))), error(lambda: bytes(Blob(Data(b"y")))), error(lambda: bytes(Blob(bytearray(b"z")))),
           error(lambda: bytes(Blob("bad")))]
    out.append(list(log))
    return out

expected = [("complex", 1j), ("complex", 2j),
            ("TypeError", "Number.__complex__() must return a complex, not float"),
            ("ValueError", "complex"), ("complex", 2j),
            ("bytes", b"x"), ("Data", b"y"),
            ("TypeError", "Blob.__bytes__() must return a bytes, not bytearray"),
            ("KeyError", "'bytes'"),
            [("complex", 1j), ("complex", Exact(2j)), ("complex", 1.5), ("complex", "bad"), ("complex", 1j),
             ("bytes", b"x"), ("bytes", b"y"), ("bytes", bytearray(b"z")), ("bytes", "bad")]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
