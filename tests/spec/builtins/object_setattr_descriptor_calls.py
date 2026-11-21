# spec: PLS-315 7.3.8, 7.3.7, 7.3.9
# description: object.__setattr__ and object.__delattr__ call a data
# descriptor's Python __set__ or __delete__, or a property's setter or
# deleter, and return None; a missing accessor's and the descriptor's
# errors pass out; the class hooks are not called.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class D:
    def __get__(s, o, t): return o.__dict__.get('_v')
    def __set__(s, o, v):
        for _ in (): pass
        log.append(('set', v)); o.__dict__['_v'] = v; return 'ignored'
    def __delete__(s, o):
        for _ in (): pass
        log.append('del')
        if o.__dict__.pop('_v', None) is None: raise AttributeError('gone')
class P:
    def g(s): return 1
    def st(s, v): log.append(('pset', v))
    def de(s): log.append('pdel')
    p = property(g, st, de)
    q = property(g)
class A:
    d = D()
    p = P.p
    q = P.q
    def __setattr__(s, n, v): log.append(('hook', n)); super().__setattr__(n, v)
    def __delattr__(s, n): log.append(('dhook', n)); super().__delattr__(n)
def t(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))
a = A()
emit(t(lambda: object.__setattr__(a, 'd', 1)), t(lambda: object.__delattr__(a, 'd')), t(lambda: object.__delattr__(a, 'd')), log)
log.clear(); a.d = 2; del a.d; emit(log)
log.clear(); emit(t(lambda: object.__setattr__(a, 'p', 3)), t(lambda: object.__delattr__(a, 'p')), log)
log.clear(); emit(t(lambda: object.__setattr__(a, 'q', 3)), t(lambda: object.__delattr__(a, 'q')), log)
log.clear(); a.p = 4; del a.p; emit(log)
log.clear(); emit(t(lambda: object.__setattr__(a, 'plain', 5)), a.plain, t(lambda: object.__delattr__(a, 'plain')), log)
EXPECTED = [
    "None None ('AttributeError', 'gone') [('set', 1), 'del', 'del']",
    "[('hook', 'd'), ('set', 2), ('dhook', 'd'), 'del']",
    "None None [('pset', 3), 'pdel']",
    '(\'AttributeError\', "property \'q\' of \'A\' object has no setter") (\'AttributeError\', "property \'q\' of \'A\' object has no deleter") []',
    "[('hook', 'p'), ('pset', 4), ('dhook', 'p'), 'pdel']",
    'None 5 None []',
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
