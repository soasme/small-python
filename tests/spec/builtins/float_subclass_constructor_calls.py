# spec: PLS-315 22.3.1, 22.3.5
# description: float.fromhex and float.from_number called on a subclass
# call it with the float they made, its Python __new__ or __init__ in
# order after the number's __float__ or __index__, its result returned
# whatever it is, and errors passing out; in a generator too.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class F(float):
    def __new__(cls, value):
        for _ in (): pass
        log.append(('new', value)); return float.__new__(cls, value + 1)
class F2(float):
    def __init__(self, value):
        for _ in (): pass
        log.append(('init', value))
class Bad(float):
    def __new__(cls, value): raise KeyError(value)
class Odd(float):
    def __new__(cls, value): return 'odd'
class Like:
    def __float__(self):
        for _ in (): pass
        log.append('float'); return 2.5
class Idx:
    def __index__(self):
        for _ in (): pass
        log.append('index'); return 7
class Wrong:
    def __float__(self): return 'x'
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return (type(r).__name__, r), log[:]
h = (1.5).hex()
for f in (lambda: F.fromhex(h), lambda: F2.fromhex(h), lambda: Bad.fromhex(h), lambda: Odd.fromhex(h), lambda: float.fromhex(h),
          lambda: F.fromhex('zz'), lambda: float.from_number(Like()), lambda: float.from_number(Idx()), lambda: F.from_number(Like()),
          lambda: F2.from_number(Idx()), lambda: float.from_number(Wrong()), lambda: float.from_number('1'), lambda: Bad.from_number(1)):
    emit(run(f))
def g(): yield run(lambda: F.from_number(Idx()))
emit(list(g()))
EXPECTED = [
    "(('F', 2.5), [('new', 1.5)])",
    "(('F2', 1.5), [('init', 1.5)])",
    "(('tuple', ('KeyError', '1.5')), [])",
    "(('str', 'odd'), [])",
    "(('float', 1.5), [])",
    "(('tuple', ('ValueError', 'invalid hexadecimal floating-point string')), [])",
    "(('float', 2.5), ['float'])",
    "(('float', 7.0), ['index'])",
    "(('F', 3.5), ['float', ('new', 2.5)])",
    "(('F2', 7.0), ['index', ('init', 7.0)])",
    "(('tuple', ('TypeError', 'Wrong.__float__() must return a float, not str')), [])",
    "(('tuple', ('TypeError', 'must be real number, not str')), [])",
    "(('tuple', ('KeyError', '1.0')), [])",
    "[(('F', 8.0), ['index', ('new', 7.0)])]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
