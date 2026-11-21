# spec: PLS-315 23.6, 24.3
# description: str and bytes % reads each mapping key through a Python
# __getitem__ when its conversion is reached, after the conversions before
# it, including a dict subclass's; a KeyError and the key checks pass out.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class M:
    def __init__(s, d): s.d = d
    def __getitem__(s, k):
        for _ in (): pass
        log.append(k)
        if k == "bad": raise KeyError(k)
        return s.d[k]
class V:
    def __str__(s): log.append("str"); return "v"
    def __repr__(s): log.append("repr"); return "V"
def t(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))
emit(t(lambda: "%(a)s-%(b)r-%(a)d" % M({"a": 1, "b": V()})), log)
log.clear(); emit(t(lambda: "%(a)s %(bad)s" % M({"a": V()})), log)
log.clear(); emit(t(lambda: b"%(a)s %(b)d" % M({b"a": b"x", b"b": 2})), log)
log.clear(); emit(t(lambda: "%(a)s %s" % M({"a": 1})), log)
log.clear(); emit(t(lambda: "%(a)*d" % M({"a": 1})), log)
class D(dict):
    def __getitem__(s, k): log.append(k); return 7
log.clear(); emit(t(lambda: "%(x)s %(y)x" % D()), log)
EXPECTED = [
    "1-V-1 ['a', 'b', 'repr', 'a']",
    '(\'KeyError\', "\'bad\'") [\'a\', \'str\', \'bad\']',
    "b'x 2' [b'a', b'b']",
    "('ValueError', 'format requires a parenthesised mapping key at position 6') ['a']",
    "('ValueError', '* cannot be used with a parenthesised mapping key at position 0') ['a']",
    "7 7 ['x', 'y']",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
