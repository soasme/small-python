# spec: PLS-315 20.5.1, 20.5.2
# description: a property whose getter is a callable instance with a
# Python __call__, which may loop, or a bound method, calls it with the
# instance read, by attribute, getattr() with or without a default,
# __get__, super() and a property subclass; its AttributeError falls back
# to the class's __getattr__, another exception propagates.
from harness import *

log = []
class G:
    def __init__(self, tag): self.tag = tag
    def __call__(self, obj):
        for _ in (): pass
        log.append(("get", self.tag, type(obj).__name__))
        if self.tag == "raise": raise KeyError("k")
        if self.tag == "attr": raise AttributeError("nope")
        return self.tag
class H:
    def m(self, obj): log.append(("m", type(obj).__name__)); return "method"
class C:
    a = property(G("a"))
    r = property(G("raise"))
    t = property(G("attr"))
    b = property(H().m)
    def __getattr__(self, name): log.append(("getattr", name)); return "fallback " + name
class D(C):
    @property
    def a(self): return "D " + super().a
class P(property): pass
class E:
    p = P(G("sub"))
def run(f):
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    out = (r, list(log)); log.clear(); return out
c = C()
out = []
for f in [lambda: c.a, lambda: c.r, lambda: c.t, lambda: c.b, lambda: getattr(c, "a"), lambda: getattr(c, "t", 5),
          lambda: getattr(c, "r", 5), lambda: C.a.__get__(c), lambda: C.a.__get__(c, C), lambda: D().a, lambda: E().p,
          lambda: [c.a for _ in range(2)], lambda: C.__dict__["a"].__get__(c)]:
    out.append(run(f))

expected = [('a', [('get', 'a', 'C')]),
 (('KeyError', "'k'"), [('get', 'raise', 'C')]),
 ('fallback t', [('get', 'attr', 'C'), ('getattr', 't')]),
 ('method', [('m', 'C')]),
 ('a', [('get', 'a', 'C')]),
 ('fallback t', [('get', 'attr', 'C'), ('getattr', 't')]),
 (('KeyError', "'k'"), [('get', 'raise', 'C')]),
 ('a', [('get', 'a', 'C')]),
 ('a', [('get', 'a', 'C')]),
 ('D a', [('get', 'a', 'D')]),
 ('sub', [('get', 'sub', 'E')]),
 (['a', 'a'], [('get', 'a', 'C'), ('get', 'a', 'C')]),
 ('a', [('get', 'a', 'C')])]
assert_eq(out, expected)
