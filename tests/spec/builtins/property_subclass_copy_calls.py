# spec: PLS-315 20.5.1
# description: getter(), setter() and deleter() of a property subclass
# make the copy by calling the subclass, its Python __new__ and __init__
# with the four values, its result returned whatever it is and errors
# passing out; the copy keeps the set name; in a generator too.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class P(property):
    def __init__(self, *args):
        for _ in (): pass
        log.append(('init', len(args))); super().__init__(*args)
class Bad(property):
    def __init__(self, *args):
        if log: raise KeyError('again')
        log.append('first'); super().__init__(*args)
class Odd(property):
    def __new__(cls, *args):
        if args and args[0] == 'x': return 'odd'
        return super().__new__(cls)
    def __init__(self, *args):
        super().__init__(*args)
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def chain():
    p = P(lambda s: 1)
    q = p.setter(lambda s, v: None).deleter(lambda s: None)
    return type(q).__name__, q.fset is not None, q.fdel is not None, q.fget is p.fget
def named():
    class A:
        x = P(lambda s: 2)
    y = A.__dict__['x'].getter(lambda s: 3)
    return y.__name__, A().x
def bad():
    p = Bad(lambda s: 1); p.setter(lambda s, v: None)
def odd():
    return Odd(lambda s: 1).getter('x')
def plain():
    p = property(lambda s: 1); return type(p.setter(None)).__name__
for f in (chain, named, bad, odd, plain): emit(run(f))
class C:
    @P
    def v(self): return 5
    @v.setter
    def v(self, val): log.append(('set', val))
c = C(); c.v = 9; emit(c.v, log)
def g(): yield run(chain)
emit(list(g()))
EXPECTED = [
    "(('P', True, True, True), [('init', 1), ('init', 4), ('init', 4)])",
    "(('x', 2), [('init', 1), ('init', 4)])",
    '((\'KeyError\', "\'again\'"), [\'first\'])',
    "('odd', [])",
    "('property', [])",
    "5 [('init', 1), ('init', 4), ('set', 9)]",
    "[(('P', True, True, True), [('init', 1), ('init', 4), ('init', 4)])]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
