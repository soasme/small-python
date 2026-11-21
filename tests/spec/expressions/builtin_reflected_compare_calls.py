# spec: PLS-315 7.2, 13.10
# description: a builtin value whose type compares as object does (a
# function, class, builtin, code object, singleton, method or wrapper)
# declines ==, != and > with an instance, whose Python reflected method
# answers; != calls __ne__.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Eq:
    def __eq__(self, o):
        for _ in (): pass
        log.append(type(o).__name__); return True
    def __ne__(self, o):
        for _ in (): pass
        log.append('ne'); return False
    def __lt__(self, o):
        for _ in (): pass
        log.append('lt'); return 'lt'
    __hash__ = None
def f(): pass
class K: pass
e = Eq()
def cmp(a, b): return (a == b, a != b, a > b)
for a in (f, K, len, print, type, None, ..., NotImplemented, K.__init__, [].append, f.__code__, range):
    del log[:]
    emit(cmp(a, e), log)
EXPECTED = [
    "(True, False, 'lt') ['function', 'ne', 'lt']",
    "(True, False, 'lt') ['type', 'ne', 'lt']",
    "(True, False, 'lt') ['builtin_function_or_method', 'ne', 'lt']",
    "(True, False, 'lt') ['builtin_function_or_method', 'ne', 'lt']",
    "(True, False, 'lt') ['type', 'ne', 'lt']",
    "(True, False, 'lt') ['NoneType', 'ne', 'lt']",
    "(True, False, 'lt') ['ellipsis', 'ne', 'lt']",
    "(True, False, 'lt') ['NotImplementedType', 'ne', 'lt']",
    "(True, False, 'lt') ['wrapper_descriptor', 'ne', 'lt']",
    "(True, False, 'lt') ['builtin_function_or_method', 'ne', 'lt']",
    "(True, False, 'lt') ['code', 'ne', 'lt']",
    "(True, False, 'lt') ['type', 'ne', 'lt']",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
