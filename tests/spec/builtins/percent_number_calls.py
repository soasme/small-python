# spec: PLS-315 23.6, 7.5.3
# description: str % of an instance for %d, %i and %u calls its Python
# __int__, else its __index__, for %o, %x and %X its __index__, and for
# %e, %f and %g its __float__, else its __index__, each of which may loop,
# once per spec, in order with %s's conversions, also through a mapping
# key and with flags, width and precision; a TypeError from the
# conversion, or a value of the wrong type, raises the spec's TypeError,
# any other exception propagates. Inside functions as at module level.
from harness import *

log = []
class N:
    def __init__(self, v): self.v = v
    def __index__(self):
        for _ in (): pass
        log.append("index")
        return self.v
class M:
    def __int__(self):
        for _ in (): pass
        log.append("int")
        return 9
    def __float__(self):
        for _ in (): pass
        log.append("float")
        return 2.5
    def __index__(self): return 4
class Bad:
    def __index__(self):
        for _ in (): pass
        return "x"
class Raise:
    def __int__(self):
        for _ in (): pass
        raise LookupError("r")
class OnlyF:
    def __float__(self):
        for _ in (): pass
        log.append("onlyf")
        return 1.25
def run():
    out = ["%d|%x|%o|%X" % (N(26), N(26), N(8), N(255)), "%5.2f %e" % (N(3), M()), "%d %i %u %x" % (M(), M(), M(), M()),
           "%(a)d-%(b)x" % {"a": N(5), "b": N(31)}, "%#x %+d %05d" % (N(17), N(3), M()), "%s %d %r" % ("s", N(2), 3),
           "%f" % OnlyF(), "%g" % N(7)]
    for f, a in (("%d", Bad()), ("%x", Bad()), ("%f", Bad()), ("%d", OnlyF())):
        try: out.append(f % a)
        except TypeError as e: out.append(str(e))
    try: "%d" % Raise()
    except LookupError as e: out.append(e.args)
    try: "%d %d" % (N(1),)
    except TypeError as e: out.append(str(e))
    out.append(log[:])
    return out

expected = ["26|1a|10|FF", " 3.00 2.500000e+00", "9 9 9 4", "5-1f", "0x11 +3 00009", "s 2 3", "1.250000", "7",
            "format argument: %d requires a real number, not Bad", "format argument: %x requires an integer, not Bad",
            "format argument: %f requires a real number, not Bad", "format argument: %d requires a real number, not OnlyF",
            ("r",), "not enough arguments for format string (got 1)",
            ["index", "index", "index", "index", "index", "float", "int", "int", "int", "index", "index", "index",
             "index", "int", "index", "onlyf", "index", "index"]]
assert_eq(run(), expected)
log.clear()
assert_eq("%x %d %.1f" % (N(255), M(), N(2)), "ff 9 2.0")
assert_eq(log, ["index", "int", "index"])
