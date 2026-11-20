# spec: PLS-315 20.5.1
# description: property() of a getter with no doc argument reads the
# getter's __doc__ once, which a Python property of its class may give and
# which may loop: its string is the property's __doc__, an AttributeError
# or None leaves it None, and another exception propagates; a doc argument
# reads nothing, and a subclass of property reads it too.
from harness import *

log = []
def doc_of(mode):
    class G:
        def __call__(self, obj): return "got"
        @property
        def __doc__(self):
            for _ in (): pass
            log.append(("doc", mode))
            if mode == "attr": raise AttributeError("x")
            if mode == "key": raise KeyError("k")
            if mode == "none": return None
            return "documented " + mode
    return G()
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def results():
    out = []
    for mode in ("str", "attr", "key", "none"):
        out.append((run(lambda: property(doc_of(mode)).__doc__), run(lambda: property(doc_of(mode), doc="given").__doc__)))
    class Getattr:
        def __getattr__(self, name):
            log.append(("getattr", name))
            return "from getattr"
        def __call__(self, o): return 1
    out.append(run(lambda: property(Getattr()).__doc__))
    def plain(self):
        "plain doc"
    out.append(run(lambda: (property(plain).__doc__, property().__doc__, property(None, None, None, "d").__doc__)))
    class Sub(property): pass
    out.append(run(lambda: Sub(doc_of("str")).__doc__))
    def inside():
        for _ in (): pass
        p = property(doc_of("in"))
        class C:
            x = p
        return C.x.__doc__, C().x
    out.append(run(inside))
    return out

expected = [
    (('documented str', [('doc', 'str')]), ('given', [])),
    ((None, [('doc', 'attr')]), ('given', [])),
    ((('KeyError', "'k'"), [('doc', 'key')]), ('given', [])),
    ((None, [('doc', 'none')]), ('given', [])),
    (None, []),
    (('plain doc', None, 'd'), []),
    ('documented str', [('doc', 'str')]),
    (('documented in', 'got'), [('doc', 'in')]),
]
assert_eq(results(), expected)
