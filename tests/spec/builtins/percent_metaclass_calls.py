# spec: PLS-315 23.6, 7.5.5, 7.5.6
# description: str % of a class whose metaclass defines a Python __str__
# or __repr__ converts it by them for %s, %r and %a, once per spec, in
# order with the other arguments' conversions, also inside a tuple, a
# list or a dict argument's repr and through a mapping key, and bytes %
# for %r; a __str__ returning no str raises TypeError and an exception of
# either method propagates. Inside a function as at module level.
from harness import *

log = []
class M(type):
    def __repr__(cls):
        for _ in (): pass
        log.append(("repr", cls.__name__))
        if cls.__name__ == "Bad": raise LookupError("repr")
        return "R" + cls.__name__
    def __str__(cls):
        for _ in (): pass
        log.append(("str", cls.__name__))
        return 5 if cls.__name__ == "Bad" else "S" + cls.__name__
A = M("A", (), {}); B = M("B", (), {}); Bad = M("Bad", (), {})
class Plain(type): pass
P = Plain("P", (), {})

def attempt(f):
    try: return f()
    except Exception as e: return type(e).__name__

def formats():
    del log[:]
    r = ["%s %r %a" % (A, B, A), "%s" % A, "%(k)s|%(k)r" % {"k": B}, "%s" % [A, B], "%r|%s" % ((A,), {A: B}),
         b"%r" % (B,), "%s %r" % (P, P) == str(P) + " " + repr(P), attempt(lambda: "%s" % Bad), attempt(lambda: "%r" % (Bad,))]
    return r, list(log)

expected = (['SA RB RA', 'SA', 'SB|RB', '[RA, RB]', '(RA,)|{RA: RB}', b'RB', True, 'TypeError', 'LookupError'], [
    ('str', 'A'), ('repr', 'B'), ('repr', 'A'), ('str', 'A'), ('str', 'B'), ('repr', 'B'),
    ('repr', 'A'), ('repr', 'B'), ('repr', 'A'), ('repr', 'A'), ('repr', 'B'), ('repr', 'B'),
    ('str', 'Bad'), ('repr', 'Bad')])
assert_eq(formats(), expected)
del log[:]
assert_eq(["%s %r %a" % (A, B, A), list(log)], ["SA RB RA", [("str", "A"), ("repr", "B"), ("repr", "A")]])
