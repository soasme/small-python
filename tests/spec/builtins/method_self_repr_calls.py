# spec: PLS-315 7.5.5, 28.4
# description: object.__str__ returns what a Python __repr__ returns,
# unchecked, and str() then refuses a non-str naming __str__; a bound
# method's repr shows its object's Python __repr__, which may loop,
# raise, return a str subclass or no str; errors pass out.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
class Sub(str): pass
log = []
class R:
    def __init__(s, r): s.r = r
    def __repr__(s):
        for _ in (): pass
        log.append("repr")
        if isinstance(s.r, BaseException): raise s.r
        return s.r
    def m(s): pass
    def __str__(s): return object.__str__(s)
def t(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))
for r in ("r", Sub("s"), 3, RuntimeError("no")):
    log.clear()
    emit(t(lambda: object.__str__(R(r))), t(lambda: str(R(r))), t(lambda: repr(R(r).m)), log)
emit(type(object.__str__(R(Sub("s")))).__name__, type(repr(R(Sub("s")).m)).__name__)
class P:
    def m(s): pass
emit(repr(P().m)[:22], str(object.__str__(P()))[:9])
class N:
    def __repr__(s): return repr(s.m) if s.deep else "n"
    deep = False
    def m(s): pass
n = N(); n.deep = True
try: repr(n)
except RecursionError: emit("recursion")
EXPECTED = [
    "r r <bound method R.m of r> ['repr', 'repr', 'repr']",
    "s s <bound method R.m of s> ['repr', 'repr', 'repr']",
    "3 ('TypeError', 'R.__str__() must return a str, not int') ('TypeError', 'R.__repr__() must return a str, not int') ['repr', 'repr', 'repr']",
    "('RuntimeError', 'no') ('RuntimeError', 'no') ('RuntimeError', 'no') ['repr', 'repr', 'repr']",
    'Sub str',
    '<bound method P.m of < <__main__',
    'recursion',
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
