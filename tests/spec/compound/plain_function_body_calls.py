# spec: PLS-315 7.4.2, 16.1
# description: a function or lambda body without a call or loop runs its
# operators, augmented assignment, subscripts, comparisons, truth tests and
# property reads through the operands' Python methods, with their errors
# passing out; inside generators and comprehensions too.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class V:
    def __init__(self, v): self.v = v
    def __add__(self, o):
        for _ in (): pass
        log.append('add'); return V(self.v + o)
    def __isub__(self, o):
        for _ in (): pass
        log.append('isub'); return self
    def __getitem__(self, k):
        for _ in (): pass
        log.append('get'); return k
    def __eq__(self, o):
        for _ in (): pass
        log.append('eq'); return True
    __hash__ = None
    def __bool__(self):
        for _ in (): pass
        log.append('bool'); return False
    @property
    def p(self):
        for _ in (): pass
        log.append('p'); return 7
def plus(x, y): return x + y
def sub(x, y):
    x -= y
    return x
def item(x): return x[3]
def same(x, y): return x == y
def truth(x): return 1 if x else 0
def prop(x): return x.p
def either(x, y): return x or y
lam = lambda x: x[1] + x.p
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    if isinstance(r, V): r = r.v
    return r, log[:]
v = V(1)
for f in (lambda: plus(v, 2), lambda: sub(v, 2), lambda: item(v), lambda: same(v, 3), lambda: truth(v), lambda: prop(v), lambda: either(v, 5),
          lambda: lam(v), lambda: plus(V(1), 'x')):
    emit(repr(run(f)))
def g(): yield run(lambda: plus(v, 2))
emit(list(g()), [run(lambda: item(v)) for _ in (0,)])
EXPECTED = [
    "(3, ['add'])",
    "(1, ['isub'])",
    "(3, ['get'])",
    "(True, ['eq'])",
    "(0, ['bool'])",
    "(7, ['p'])",
    "(5, ['bool'])",
    "(8, ['get', 'p'])",
    '((\'TypeError\', "unsupported operand type(s) for +: \'int\' and \'str\'"), [\'add\'])',
    "[(3, ['add'])] [(3, ['get'])]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
