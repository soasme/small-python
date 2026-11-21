# spec: PLS-315 7.6.2, 13.9
# description: A set's or frozenset's |, &, - and ^, and a dict's or
# frozendict's |, decline an instance of another builtin's subclass, a
# dict's, set's, list's or int's, whose Python reflected method, which may
# loop or return NotImplemented, is then called; in place too, and with
# a set's or dict's subclass on the left.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
def reflected(name):
    def method(self, other):
        for _ in (): pass
        log.append((type(self).__name__, name))
        return name
    return method
class S(set): pass
class D(dict): pass
class FD(frozendict): pass
class FS(frozenset): pass
class L(list): pass
class I(int): pass
for cls in (S, D, FD, FS, L, I):
    for name in ('__ror__', '__rand__', '__rsub__', '__rxor__'):
        setattr(cls, name, reflected(name))
class Declined(dict):
    def __ror__(self, other):
        for _ in (): pass
        log.append('declined'); return NotImplemented
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def ior(x, y):
    x |= y
    return x
for f in (lambda: {1} | D(z=9), lambda: {'a': 1} | S({2}), lambda: {1} & FD(a=1), lambda: {1} - L([1]), lambda: {1} ^ I(3),
          lambda: frozenset({1}) | D(), lambda: frozendict(a=1) | S(), lambda: {'a': 1} | FS(), lambda: {'a': 1} | L(),
          lambda: {1} | Declined(), lambda: ior({1}, D(z=1)), lambda: ior({'a': 1}, S({2})), lambda: ior(S({1}), D()),
          lambda: ior(D(a=1), S({1})), lambda: S({1}) | D(), lambda: D() | S(), lambda: {1} | S({2}), lambda: {'a': 1} | D(z=9)):
    r = run(f)
    emit(r if not isinstance(r[0], (set, frozenset, dict, frozendict)) else (type(r[0]).__name__, sorted(r[0]), r[1]))
EXPECTED = [
    "('__ror__', [('D', '__ror__')])",
    "('__ror__', [('S', '__ror__')])",
    "('__rand__', [('FD', '__rand__')])",
    "('__rsub__', [('L', '__rsub__')])",
    "('__rxor__', [('I', '__rxor__')])",
    "('__ror__', [('D', '__ror__')])",
    "('__ror__', [('S', '__ror__')])",
    "('__ror__', [('FS', '__ror__')])",
    "('__ror__', [('L', '__ror__')])",
    '((\'TypeError\', "unsupported operand type(s) for |: \'set\' and \'Declined\'"), [\'declined\'])',
    "('__ror__', [('D', '__ror__')])",
    "(('TypeError', 'object is not iterable'), [])",
    "('__ror__', [('D', '__ror__')])",
    "(('TypeError', 'object is not iterable'), [])",
    "('__ror__', [('D', '__ror__')])",
    "('__ror__', [('S', '__ror__')])",
    "('__ror__', [('S', '__ror__')])",
    "('__ror__', [('D', '__ror__')])",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
