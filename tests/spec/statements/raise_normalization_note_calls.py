# spec: PLS-315 14.8, 21.1.4
# description: when raising a class whose call makes no instance of it
# fails, the note on that error shows the made exception's repr, a Python
# __repr__ of it or of its arguments called once, "<unknown>" when it
# raises; the error itself is raised; inside generators and
# comprehensions too.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Shown(KeyError):
    def __repr__(self):
        for _ in (): pass
        log.append('repr'); return 'SHOWN'
class Hidden(KeyError):
    def __repr__(self): log.append('hid'); raise ValueError('h')
class Inner:
    def __repr__(self):
        for _ in (): pass
        log.append('inner'); return 'IN'
def maker(made):
    class Strict(Exception):
        def __new__(cls):
            for _ in (): pass
            log.append('new'); return made
    return Strict
def run(made):
    del log[:]
    try: raise maker(made)
    except BaseException as e: return (type(e).__name__, str(e), getattr(e, '__notes__', None), log[:])
for made in (Shown('s'), Hidden('h'), KeyError(Inner()), KeyError(Inner(), Shown('z')), 5, Shown('t')):
    emit(repr(run(made)))
def g(): yield run(Shown('g'))
emit(list(g()), [run(KeyError(Inner())) for _ in (0,)])
EXPECTED = [
    "('TypeError', 'maker.<locals>.Strict.__new__() takes 1 positional argument but 2 were given', ['Normalization failed: type=Strict args=SHOWN'], ['new', 'repr'])",
    "('TypeError', 'maker.<locals>.Strict.__new__() takes 1 positional argument but 2 were given', ['Normalization failed: type=Strict args=<unknown>'], ['new', 'hid'])",
    "('TypeError', 'maker.<locals>.Strict.__new__() takes 1 positional argument but 2 were given', ['Normalization failed: type=Strict args=KeyError(IN)'], ['new', 'inner'])",
    "('TypeError', 'maker.<locals>.Strict.__new__() takes 1 positional argument but 2 were given', ['Normalization failed: type=Strict args=KeyError(IN, SHOWN)'], ['new', 'inner', 'repr'])",
    '(\'TypeError\', "calling <class \'__main__.maker.<locals>.Strict\'> should have returned an instance of BaseException, not <class \'int\'>", None, [\'new\'])',
    "('TypeError', 'maker.<locals>.Strict.__new__() takes 1 positional argument but 2 were given', ['Normalization failed: type=Strict args=SHOWN'], ['new', 'repr'])",
    "[('TypeError', 'maker.<locals>.Strict.__new__() takes 1 positional argument but 2 were given', ['Normalization failed: type=Strict args=SHOWN'], ['new', 'repr'])] [('TypeError', 'maker.<locals>.Strict.__new__() takes 1 positional argument but 2 were given', ['Normalization failed: type=Strict args=KeyError(IN)'], ['new', 'inner'])]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
