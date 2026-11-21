# spec: PLS-315 16.4.1, 7.6.3, 7.3.4
# description: A class body with no call and no loop runs its operators,
# subscripts, comparisons and attribute reads like any other code: their
# Python special methods, which may loop, run in order, and an error one
# raises is caught by a try in the body. Such a class statement calls a
# Python __build_class__ of its builtins, which may loop, before its body.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class N:
    def __init__(self, v): self.v = v
    def __add__(self, o):
        for _ in (): pass
        log.append(("add", self.v, o)); return N(self.v + o)
    def __getitem__(self, k):
        for _ in (): pass
        log.append(("item", k)); return k * 2
    def __lt__(self, o):
        for _ in (): pass
        log.append(("lt", o)); return True
    def __getattr__(self, name):
        for _ in (): pass
        log.append(("attr", name)); return name
    def __neg__(self):
        for _ in (): pass
        log.append("neg"); return 0
a = N(1)
class C:
    x = a + 2
    y = a[3]
    z = a < 4
    w = a.missing
    u = -a
emit(C.x.v, C.y, C.z, C.w, C.u, log)
log.clear()
def f():
    class D:
        p = a + 5
        q = a.other
    return D
D = f(); emit(D.p.v, D.q, log)
log.clear()
class Bad:
    try:
        r = a + "s"
    except TypeError as e:
        r = type(e).__name__
emit(Bad.r, log)
log.clear()
built = __build_class__
def builder(func, name, *bases, **kw):
    for _ in (): pass
    log.append(("build", name, bases, kw))
    return built(func, name, *bases, **kw)
ns = {"__builtins__": dict(vars(built.__self__), __build_class__=builder), "a": a, "__name__": "m"}
exec("class E:\n    e = a + 7\nclass F(E):\n    pass\ndef g():\n    class G: pass\n    return G\nH = g()", ns)
emit(ns["E"].e.v, ns["F"].__bases__[0] is ns["E"], ns["H"].__qualname__, [(x[0], x[1], len(x[2]), x[3]) for x in log[:1]], [x[1] for x in log if x[0] == "build"])
EXPECTED = [
    "3 6 True missing 0 [('add', 1, 2), ('item', 3), ('lt', 4), ('attr', 'missing'), 'neg']",
    "6 other [('add', 1, 5), ('attr', 'other')]",
    "TypeError [('add', 1, 's')]",
    "8 True g.<locals>.G [('build', 'E', 0, {})] ['E', 'F', 'G']",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
