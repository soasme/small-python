# spec: PLS-315 22.4.1
# description: complex.from_number converts by a Python __complex__,
# __float__ or __index__, which may loop, once, refuses strings and a
# bad __complex__ result, and called on a subclass then calls the
# subclass, whose Python __new__ runs once, with the complex number.
from harness import *

log = []
class WithComplex:
    def __init__(s, v): s.v = v
    def __complex__(s):
        for _ in (): pass
        log.append("complex")
        return s.v
class WithFloat:
    def __init__(s, v): s.v = v
    def __float__(s):
        for _ in (): pass
        log.append("float")
        return s.v
class WithIndex:
    def __init__(s, v): s.v = v
    def __index__(s):
        for _ in (): pass
        log.append("index")
        return s.v
class Sub(complex): pass
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
class Made(complex):
    def __new__(cls, v):
        for _ in (): pass
        log.append("new")
        return super().__new__(cls, v)
for cls, name in ((complex, "complex"), (Sub, "Sub")):
    assert_eq([run(lambda: cls.from_number(WithComplex(3+2j))), run(lambda: cls.from_number(WithFloat(1.5))),
               run(lambda: cls.from_number(WithIndex(4))), run(lambda: cls.from_number(WithComplex("x"))),
               run(lambda: cls.from_number("1")), run(lambda: type(cls.from_number(2)).__name__)],
              [((3+2j), ["complex"]), ((1.5+0j), ["float"]), ((4+0j), ["index"]),
               (("TypeError", "WithComplex.__complex__() must return a complex, not str"), ["complex"]),
               (("TypeError", "must be real number, not str"), []), (name, [])])
def inside():
    for _ in (): pass
    return complex.from_number(WithFloat(2.5)), complex.from_number(WithComplex(1j)).imag
assert_eq(run(inside), (((2.5+0j), 1.0), ["float", "complex"]))
assert_eq([run(lambda: Made.from_number(WithFloat(0.5))), run(lambda: type(Made.from_number(1j)).__name__), run(lambda: Sub.from_number(1j) == 1j)],
          [((0.5+0j), ["float", "new"]), ("Made", ["new"]), (True, [])])
