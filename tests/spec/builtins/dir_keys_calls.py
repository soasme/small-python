# spec: PLS-315 19.3.12, 7.7.6
# description: dir() calls a Python __dir__, an instance's, a metaclass's
# or a module's own, and lists and sorts what it gives, iterating a
# generator or iterable; dir() of locals that are a mapping calls its
# Python keys(), its own or its class's; errors pass out.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class D:
    def __init__(s, r): s.r = r
    def __dir__(s):
        for _ in (): pass
        log.append('dir')
        if isinstance(s.r, BaseException): raise s.r
        return s.r
def gen():
    log.append('gen'); yield 'b'; yield 'a'
class It:
    def __iter__(s): log.append('iter'); return iter(['z', 'y'])
def t(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))
for r in (['b', 'a'], ('c', 'b'), gen(), It(), {'k': 1, 'j': 2}, 5, RuntimeError('no'), [1, 'a']):
    log.clear(); emit(t(lambda: dir(D(r))), log)
class M(type):
    def __dir__(cls): log.append('meta'); return ['m2', 'm1']
class K(metaclass=M): pass
log.clear(); emit(dir(K), log)
class NS:
    def __init__(s): s.d = {'q': 1, 'p': 2}
    def __getitem__(s, k): return s.d[k]
    def keys(s):
        for _ in (): pass
        log.append('keys'); return (k for k in s.d)
log.clear(); emit(eval('dir()', {}, NS()), log)
class NS2(NS):
    def keys(s): log.append('keys2'); raise ValueError('k')
log.clear(); emit(t(lambda: eval('dir()', {}, NS2())), log)
n3 = NS(); n3.keys = lambda: ['own']
log.clear(); emit(eval('dir()', {}, n3), log)
mod = type(__import__('builtins'))('m')
def mdir():
    for _ in (): pass
    log.append('mdir'); return ['zz', 'aa']
mod.__dir__ = mdir
log.clear(); emit(dir(mod), log)
EXPECTED = [
    "['a', 'b'] ['dir']",
    "['b', 'c'] ['dir']",
    "['a', 'b'] ['dir', 'gen']",
    "['y', 'z'] ['dir', 'iter']",
    "['j', 'k'] ['dir']",
    '(\'TypeError\', "\'int\' object is not iterable") [\'dir\']',
    "('RuntimeError', 'no') ['dir']",
    '(\'TypeError\', "\'<\' not supported between instances of \'str\' and \'int\'") [\'dir\']',
    "['m1', 'm2'] ['meta']",
    "['p', 'q'] ['keys']",
    "('ValueError', 'k') ['keys2']",
    "['own'] []",
    "['aa', 'zz'] ['mdir']",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
