# spec: PLS-315 16.1.2, 16.4.1, 16.5
# description: A decorator that is a class, a callable instance or a bound
# method is called like a function decorator, the last first, its Python
# __init__ or __call__, which may loop, running in order, in a function,
# a generator or a class statement; an error it raises passes out, its
# traceback naming the decorator's own line.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Deco:
    def __init__(self, f):
        for _ in (): pass
        log.append(("init", f.__name__)); self.f = f
    def __call__(self, *a): return self.f(*a)
class Wrap:
    def __call__(self, f):
        for _ in (): pass
        log.append(("call", getattr(f, "__name__", type(f).__name__))); return f
@Deco
def g(x): return x + 1
@Wrap()
@Deco
def h(x): return x * 2
@Wrap()
class K: pass
emit(g(1), h.f(3), K.__name__, log)
class Meth:
    def deco(self, f):
        for _ in (): pass
        log.append(("meth", f.__name__)); return f
log.clear()
@Meth().deco
def k(): pass
@staticmethod
def s(): return 5
emit(k.__name__, s(), log)
class Bad:
    def __init__(self, f): raise ValueError("bad " + f.__name__)
try:
    @Bad
    def q(): pass
except ValueError as e: emit(e)
def gen():
    @Wrap()
    def inner(): pass
    yield inner.__name__
    @Deco
    def inner2(): pass
    yield inner2.f.__name__
emit(list(gen()), log)
class Wrap:
    def __call__(self, f):
        return f.missing
def plain(f): return f.missing
for src in ("@Wrap()\n@plain\ndef h(): pass", "@plain\n\n@Wrap()\ndef h(): pass", "@Wrap()\nclass K: pass"):
    try: exec(src, {"Wrap": Wrap, "plain": plain})
    except AttributeError as e: emit(e.__traceback__.tb_next.tb_lineno, e)
EXPECTED = [
    "2 6 K [('init', 'g'), ('init', 'h'), ('call', 'Deco'), ('call', 'K')]",
    "k 5 [('meth', 'k')]",
    'bad q',
    "['inner', 'inner2'] [('meth', 'k'), ('call', 'inner'), ('init', 'inner2')]",
    "2 'function' object has no attribute 'missing'",
    "3 'function' object has no attribute 'missing'",
    "1 type object 'K' has no attribute 'missing'",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
