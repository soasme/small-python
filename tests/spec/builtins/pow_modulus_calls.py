# spec: PLS-315 19.3.30, 7.6.2, 22.4.1
# description: pow(x, y, z) of an instance with a Python __pow__, which
# may loop, calls it with the exponent and the modulus; NotImplemented
# goes on to the built-in power slots, int's taking an int subclass's
# value, float's refusing a modulus and complex's declining a base or
# exponent that is not a number, then TypeError naming the three types.
# An instance exponent's __rpow__ is called with no modulus. Inside
# functions as at module level.
from harness import *

log = []
class P:
    def __init__(self, r): self.r = r
    def __pow__(self, b, m=None):
        for _ in (): pass
        log.append(tuple("P" if isinstance(v, P) else v for v in (b, m)))
        if self.r == "raise": raise LookupError("p")
        return NotImplemented if self.r == "ni" else self.r
    def __rpow__(self, a, m=None):
        log.append("rpow")
        return "r"
class IP(int):
    def __pow__(self, b, m=None):
        for _ in (): pass
        log.append(("ip", b, m))
        return NotImplemented
class Two:
    def __pow__(self, b):
        for _ in (): pass
        return 1
def t(f):
    try: r = f()
    except Exception as e: r = type(e).__name__ + ": " + str(e)
    out = (r, log[:]); del log[:]; return out
def results():
    return [t(lambda: pow(P(7), 2, 5)), t(lambda: pow(P("ni"), 2, 5)), t(lambda: pow(P("ni"), 2.0, 5)), t(lambda: pow(P("ni"), 2, 1j)),
            t(lambda: pow(P("raise"), 2, 5)), t(lambda: pow(P(1), 2, None)), t(lambda: pow(IP(3), 2, 5)), t(lambda: pow(IP(3), 2.5, 5)),
            t(lambda: pow(Two(), 2, 5)), t(lambda: pow(P(1), P(2), 5)), t(lambda: pow(2, P(3), 5)), t(lambda: pow(P(9), 2, P(1))),
            t(lambda: pow(base=P(4), exp=2, mod=5)), t(lambda: pow(P(4), 2, mod=5)), t(lambda: pow(P("ni"), "a", "b")),
            t(lambda: pow(P(5), True, 3)),
            t(lambda: direct())] + [t(f) for f in (lambda: pow(P(), 2, 1j), lambda: pow(Q(), 2, 1j), lambda: pow(1j, Q(), 2), lambda: pow(1j, 2, Q()), lambda: pow(2, 1j, Q()), lambda: pow("a", 1j, 2), lambda: pow(1j, "a", 2), lambda: pow(1, 2, 1j), lambda: pow(Q(), 2.0, 1), lambda: pow(2.0, Q(), 1))]

class Q:
    pass

def direct():
    return pow(P(1), 2, 3), pow(IP(3), 2, 5)

expected = [(7, [(2, 5)]), ("TypeError: unsupported operand type(s) for ** or pow(): 'P', 'int', 'int'", [(2, 5)]),
            ('TypeError: pow() 3rd argument not allowed unless all arguments are integers', [(2.0, 5)]),
            ("TypeError: unsupported operand type(s) for ** or pow(): 'P', 'int', 'complex'", [(2, 1j)]),
            ('LookupError: p', [(2, 5)]), (1, [(2, None)]), (4, [('ip', 2, 5)]),
            ('TypeError: pow() 3rd argument not allowed unless all arguments are integers', [('ip', 2.5, 5)]),
            ('TypeError: Two.__pow__() takes 2 positional arguments but 3 were given', []), (1, [('P', 5)]),
            ('r', ['rpow']), (9, [(2, 'P')]), (4, [(2, 5)]), (4, [(2, 5)]),
            ("TypeError: unsupported operand type(s) for ** or pow(): 'P', 'str', 'str'", [('a', 'b')]),
            (5, [(True, 3)]), ((1, 4), [(2, 3), ('ip', 2, 5)]),
            ("TypeError: P.__init__() missing 1 required positional argument: 'r'", []),
            ("TypeError: unsupported operand type(s) for ** or pow(): 'Q', 'int', 'complex'", []),
            ("TypeError: unsupported operand type(s) for ** or pow(): 'complex', 'Q', 'int'", []),
            ('ValueError: complex modulo', []), ('ValueError: complex modulo', []),
            ("TypeError: unsupported operand type(s) for ** or pow(): 'str', 'complex', 'int'", []),
            ("TypeError: unsupported operand type(s) for ** or pow(): 'complex', 'str', 'int'", []),
            ('ValueError: complex modulo', []),
            ('TypeError: pow() 3rd argument not allowed unless all arguments are integers', []),
            ('TypeError: pow() 3rd argument not allowed unless all arguments are integers', [])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
