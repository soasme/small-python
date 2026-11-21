# spec: PLS-315 20.6, 27.1.6
# description: Calling a staticmethod object calls its function with the
# arguments as given, a callable instance's Python __call__, a builtin,
# or a nested staticmethod's function; so do a subclass's instance and
# its super().__call__, and a map of one, unpacked or listed; a
# non-callable function raises; in a generator too.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Fn:
    def __call__(self, *a, **k):
        for _ in (): pass
        log.append((a, k)); return len(a)
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
s = staticmethod(Fn())
class SM(staticmethod): pass
class Own(staticmethod):
    def __call__(self, *a):
        log.append('own'); return super().__call__(*a)
sub = SM(Fn())
own = Own(Fn())
def unpacked():
    a, b = map(s, [1, (2, 3)]); return a, b
ss = staticmethod(staticmethod(Fn()))
for f in (lambda: s(1, 2), lambda: s(), lambda: s(*[1], **{'k': 2}), lambda: ss(3), lambda: staticmethod(len)('ab'),
          lambda: staticmethod(len)(), lambda: staticmethod(5)(), lambda: staticmethod(lambda x: x * 2)(4),
          lambda: staticmethod(staticmethod(lambda: 'in'))(), lambda: list(map(s, [7, 8])), unpacked, lambda: sub(1), lambda: sub(*(2, 3)), lambda: own(4), lambda: SM(len)('xyz')):
    emit(run(f))
def g(): yield run(lambda: s(9))
emit(list(g()))
EXPECTED = [
    '(2, [((1, 2), {})])',
    '(0, [((), {})])',
    "(1, [((1,), {'k': 2})])",
    '(1, [((3,), {})])',
    '(2, [])',
    "(('TypeError', 'len() takes exactly one argument (0 given)'), [])",
    '((\'TypeError\', "\'int\' object is not callable"), [])',
    '(8, [])',
    "('in', [])",
    '([1, 1], [((7,), {}), ((8,), {})])',
    '((1, 1), [((1,), {}), (((2, 3),), {})])',
    '(1, [((1,), {})])',
    '(2, [((2, 3), {})])',
    "(1, ['own', ((4,), {})])",
    '(3, [])',
    '[(1, [((9,), {})])]',
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
