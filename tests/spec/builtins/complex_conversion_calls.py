# spec: PLS-315 22.4.1, 22.3.1
# description: complex(x) of an object without __complex__ converts the
# float its __float__ returns, else the int its __index__ returns, each
# of which may loop and whose wrong result type, exception or overflow
# propagates. Given two parts, the real part's __complex__ runs first,
# then both parts must be numbers before either converts, the imaginary
# part never by __complex__. Inside functions as at module level.
from harness import *

log = []
class F:
    def __init__(self, v): self.v = v
    def __float__(self):
        for _ in (): pass
        log.append("float")
        if self.v == "raise": raise LookupError("f")
        return self.v
class I:
    def __init__(self, v): self.v = v
    def __index__(self):
        for _ in (): pass
        log.append("index")
        return self.v
class FI(F):
    def __index__(self):
        log.append("index")
        return 9
class FS(float): pass
def t(f):
    try: r = f()
    except Exception as e: r = type(e).__name__ + ": " + str(e)
    out = (r, log[:]); del log[:]; return out
def results():
    return [t(lambda: complex(F(2.5))), t(lambda: complex(F("x"))), t(lambda: complex(F("raise"))), t(lambda: complex(F(3))),
            t(lambda: complex(I(4))), t(lambda: complex(I(1.5))), t(lambda: complex(I(1 << 2000))),
            t(lambda: complex(FI(1.5))), t(lambda: complex(F(1.0), 2)), t(lambda: complex(1, I(2))),
            t(lambda: complex(real=F(2.0))), t(lambda: complex(I(-3))),
            t(lambda: direct())] + pairs()

class N:
    pass

class C:
    def __complex__(self):
        log.append("complex")
        return 1j
    def __float__(self):
        log.append("cfloat")
        return 2.0

def pairs():
    return [t(lambda: complex(F(1.0), N())), t(lambda: complex(N(), F(1.0))), t(lambda: complex(F(1.0), C())),
       t(lambda: complex(I(3), I(3))), t(lambda: complex(F(1.0), "1")),
       t(lambda: complex("1", F(1.0))), t(lambda: complex(C(), N())), t(lambda: complex(imag=F(1.0))), t(lambda: complex(real=I(3), imag=I(3)))]

def direct():
    return complex(F(1.5)), complex(I(2))

expected = [((2.5+0j), ['float']), ('TypeError: F.__float__() must return a float, not str', ['float']),
            ('LookupError: f', ['float']), ('TypeError: F.__float__() must return a float, not int', ['float']),
            ((4+0j), ['index']), ('TypeError: I.__index__() must return an int, not float', ['index']),
            ('OverflowError: int too large to convert to float', ['index']), ((1.5+0j), ['float']), ((1+2j), ['float']),
            ((1+2j), ['index']), ((2+0j), ['float']), ((-3+0j), ['index']), (((1.5+0j), (2+0j)), ['float', 'index']),
            ("TypeError: complex() argument 'imag' must be a real number, not N", []),
            ("TypeError: complex() argument 'real' must be a real number, not N", []), ((1+2j), ['float', 'cfloat']),
            ((3+3j), ['index', 'index']), ("TypeError: complex() argument 'imag' must be a real number, not str", []),
            ("TypeError: complex() argument 'real' must be a real number, not str", []),
            ("TypeError: complex() argument 'imag' must be a real number, not N", ['complex']), (1j, ['float']),
            ((3+3j), ['index', 'index'])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
