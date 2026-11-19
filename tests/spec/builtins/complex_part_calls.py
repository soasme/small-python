# spec: PLS-315 22.4.1, 22.3.1
# description: complex(real, imag), and complex() naming either part by
# keyword, positionally, starred or through a mapping, converts its parts
# by their Python methods in order: the real part's __complex__ first,
# then both parts checked to be numbers, then the real part's __float__
# or __index__, then the imaginary part's. Each method may loop, pause
# in a generator, call complex() again or recurse, and its error or wrong
# result type propagates; the imaginary part converts by __float__ even
# when it has __complex__, and a complex real part's imaginary part adds to
# it, keeping a signed zero. Inside functions as at module
# level.
from harness import *

log = []
class F:
    def __init__(self, v): self.v = v
    def __float__(self):
        for _ in range(2): pass
        log.append(("float", self.v))
        if self.v == "raise": raise LookupError("f")
        return self.v
class I:
    def __init__(self, v): self.v = v
    def __index__(self):
        for _ in range(2): pass
        log.append(("index", self.v))
        return self.v
class C:
    def __init__(self, v): self.v = v
    def __complex__(self):
        for _ in range(2): pass
        log.append(("complex", self.v))
        return self.v
    def __float__(self):
        log.append("cfloat")
        return 9.0
class Nested:
    def __float__(self):
        for _ in range(2): pass
        log.append("nested")
        return complex(F(2.0), I(3)).imag
class Deep:
    def __float__(self):
        for _ in range(2): pass
        return complex(self, 0).real
class N:
    pass

def t(f):
    try: r = f()
    except Exception as e: r = type(e).__name__ + ": " + str(e)
    out = (r, log[:]); del log[:]; return out

def calls():
    return [t(lambda: complex(F(1.5), I(2))), t(lambda: complex(C(1 + 2j), F(3.0))), t(lambda: complex(C(1 + 2j), C(5j))),
            t(lambda: complex(1, C(5j))), t(lambda: complex(C(4j), N())), t(lambda: complex(F(1.0), N())),
            t(lambda: complex(N(), F(1.0))), t(lambda: complex(F("raise"), I(1))), t(lambda: complex(F(1.0), F("raise"))),
            t(lambda: complex(C(2.0), 1)), t(lambda: complex(F(1.0), I(2.5))), t(lambda: complex(I(1 << 2000), 1)),
            t(lambda: complex(F(-0.0), -0.0)), t(lambda: complex(C(-0.0j), -0.0)), t(lambda: complex(Nested(), F(1.0))),
            t(lambda: complex(real=F(2.0))), t(lambda: complex(imag=I(4))), t(lambda: complex(real=I(1), imag=F(2.0))),
            t(lambda: complex(F(1.0), imag=C(1j))), t(lambda: complex(*[I(7), F(8.0)])), t(lambda: complex(**{"imag": F(6.0)})),
            t(lambda: complex(real=F(1.0), real2=2)), t(lambda: complex(F(1.0), 2, 3))]

expected = [((1.5+2j), [("float", 1.5), ("index", 2)]),
            ((1+5j), [("complex", 1 + 2j), ("float", 3.0)]),
            ((1+11j), [("complex", 1 + 2j), "cfloat"]),
            ((1+9j), ["cfloat"]),
            ("TypeError: complex() argument 'imag' must be a real number, not N", [("complex", 4j)]),
            ("TypeError: complex() argument 'imag' must be a real number, not N", []),
            ("TypeError: complex() argument 'real' must be a real number, not N", []),
            ("LookupError: f", [("float", "raise")]),
            ("LookupError: f", [("float", 1.0), ("float", "raise")]),
            ("TypeError: C.__complex__() must return a complex, not float", [("complex", 2.0)]),
            ("TypeError: I.__index__() must return an int, not float", [("float", 1.0), ("index", 2.5)]),
            ("OverflowError: int too large to convert to float", [("index", 1 << 2000)]),
            (complex(-0.0, -0.0), [("float", -0.0)]),
            (complex(-0.0, -0.0), [("complex", -0j)]),
            ((3+1j), ["nested", ("float", 2.0), ("index", 3), ("float", 1.0)]),
            ((2+0j), [("float", 2.0)]),
            (4j, [("index", 4)]),
            ((1+2j), [("index", 1), ("float", 2.0)]),
            ((1+9j), [("float", 1.0), "cfloat"]),
            ((7+8j), [("index", 7), ("float", 8.0)]),
            (6j, [("float", 6.0)]),
            ("TypeError: complex() got an unexpected keyword argument 'real2'. Did you mean 'real'?", []),
            ("TypeError: complex() takes at most 2 arguments (3 given)", [])]

def paused():
    # Each part's method runs while a generator is suspended around it.
    def gen():
        yield complex(F(1.0), I(2))
        yield complex(imag=F(3.0), real=C(1j))
    return list(gen()), log[:]

def results():
    out = calls(), paused()
    del log[:]
    return out

expected_all = (expected, ([(1+2j), 4j], [("float", 1.0), ("index", 2), ("complex", 1j), ("float", 3.0)]))

def main():
    return results()

assert_eq(main(), expected_all)
assert_eq(results(), expected_all)

try:
    complex(Deep(), 0)
except RecursionError:
    deep = "RecursionError"
assert_eq(deep, "RecursionError")
