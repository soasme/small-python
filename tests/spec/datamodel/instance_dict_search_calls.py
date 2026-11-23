# spec: PLS-315 7.3.5, 10.1.1
# description: an attribute read of an instance whose __dict__ holds a
# key other than str, whether by a dot or by getattr() or hasattr(),
# searches the __dict__ for the name by each same-hash key's Python
# __eq__ after its class's data descriptors and before its non-data
# descriptors, methods and class attributes, a method call's too, a key of
# the same hash that is not equal included (CPython may retry a failed
# specialized lookup, so a miss is recorded once); a miss goes on to them
# and to __getattr__, those the class had before the search. Inside
# functions and generators as at module level.
from harness import *
log = []
class K:
    def __init__(self, n): self.n = n
    def __hash__(self): return hash(self.n)
    def __eq__(self, o):
        for _ in (): pass
        log.append(("eq", self.n, o))
        return self.n == o
class Miss(K):
    def __eq__(self, o):
        for _ in (): pass
        log.append(("miss", self.n, o)) if ("miss", self.n, o) not in log else None
        return False
    __hash__ = K.__hash__
class NonData:
    def __get__(self, obj, cls): log.append("nget"); return "N"
class Data:
    def __get__(self, obj, cls): log.append("dget"); return "D"
    def __set__(self, obj, v): pass
class C:
    nd = NonData()
    dd = Data()
    k = "class"
    def __getattr__(self, name):
        for _ in (): pass
        log.append(("getattr", name))
        return "ga-" + name
    def m(self): return "m"
    def meth(self, *args): return ("meth",) + args
class E:
    @property
    def p(self): return "p"
c = C()
for name, value in (("x", 1), ("nd", 2), ("dd", 3), ("m", 4), ("y", 5)):
    c.__dict__[K(name)] = value
c.__dict__[K("f")] = lambda *args: ("f",) + args
for name in ("k", "zz", "q", "m2", "meth"):
    c.__dict__[Miss(name)] = 0
c.s = 6
e = E()
e.__dict__[K("w")] = 7
e.__dict__[Miss("v")] = 8
# A key whose __eq__ deletes the class's attributes: the read goes on with
# what the class had before the search.
class Deleting(K):
    def __eq__(self, o):
        for _ in (): pass
        for name in ("nd", "meth", "__getattr__"):
            if name in vars(G): delattr(G, name)
        log.append(("deleted", o)) if ("deleted", o) not in log else None
        return False
    __hash__ = K.__hash__
class G:
    nd = NonData()
    def meth(self): return "meth"
    def __getattr__(self, name): return "ga-" + name
def deleting(name):
    global G
    class G:
        nd = NonData()
        def meth(self): return "meth"
        def __getattr__(self, name): return "ga-" + name
    g = G()
    g.__dict__[Deleting(name)] = 0
    return g
def run(f):
    del log[:]
    try: result = f()
    except (AttributeError, TypeError) as error: result = (type(error).__name__, str(error))
    return result, list(log)
def cases():
    return [run(lambda: c.x), run(lambda: c.nd), run(lambda: c.dd), run(lambda: c.m), run(lambda: c.k),
            run(lambda: c.s), run(lambda: c.zz), run(lambda: getattr(c, "y")), run(lambda: getattr(c, "q", 0)),
            run(lambda: hasattr(c, "x")), run(lambda: getattr(e, "w", 0)), run(lambda: getattr(e, "v", 0)),
            run(lambda: hasattr(e, "v")), run(lambda: e.p), run(lambda: e.v), run(lambda: getattr(e, "v")),
            run(lambda: c.m2), run(lambda: getattr(c, "zz")), run(lambda: c.f()), run(lambda: c.f(len([1]), 2)),
            run(lambda: c.meth()), run(lambda: c.meth(len([1]))), run(lambda: c.zz()), run(lambda: e.v()),
            run(lambda: deleting("nd").nd), run(lambda: getattr(deleting("nd"), "nd")), run(lambda: deleting("meth").meth()),
            run(lambda: deleting("zz").zz), run(lambda: getattr(deleting("zz"), "zz", 0)), run(lambda: deleting("nd").nd + deleting("zz").zz)]
def gen():
    yield cases()
expected = [(1, [('eq', 'x', 'x')]),
            (2, [('eq', 'nd', 'nd')]),
            ('D', ['dget']),
            (4, [('eq', 'm', 'm')]),
            ('class', [('miss', 'k', 'k')]),
            (6, []),
            ('ga-zz', [('miss', 'zz', 'zz'), ('getattr', 'zz')]),
            (5, [('eq', 'y', 'y')]),
            ('ga-q', [('miss', 'q', 'q'), ('getattr', 'q')]),
            (True, [('eq', 'x', 'x')]),
            (7, [('eq', 'w', 'w')]),
            (0, [('miss', 'v', 'v')]),
            (False, [('miss', 'v', 'v')]),
            ('p', []),
            (('AttributeError', "'E' object has no attribute 'v'"), [('miss', 'v', 'v')]),
            (('AttributeError', "'E' object has no attribute 'v'"), [('miss', 'v', 'v')]),
            ('ga-m2', [('miss', 'm2', 'm2'), ('getattr', 'm2')]),
            ('ga-zz', [('miss', 'zz', 'zz'), ('getattr', 'zz')]),
            (('f',), [('eq', 'f', 'f')]),
            (('f', 1, 2), [('eq', 'f', 'f')]),
            (('meth',), [('miss', 'meth', 'meth')]),
            (('meth', 1), [('miss', 'meth', 'meth')]),
            (('TypeError', "'str' object is not callable"), [('miss', 'zz', 'zz'), ('getattr', 'zz')]),
            (('AttributeError', "'E' object has no attribute 'v'"), [('miss', 'v', 'v')]),
            ('N', [('deleted', 'nd'), 'nget']),
            ('N', [('deleted', 'nd'), 'nget']),
            ('meth', [('deleted', 'meth')]),
            ('ga-zz', [('deleted', 'zz')]),
            ('ga-zz', [('deleted', 'zz')]),
            ('Nga-zz', [('deleted', 'nd'), 'nget', ('deleted', 'zz')])]
assert_eq(cases(), expected)
assert_eq(next(gen()), expected)
def outer():
    return cases()
assert_eq(outer(), expected)

# A key equal to the name but no str finds it in a globals dict and an
# instance __dict__; an unequal one is passed over.
class NamedKey:
    def __hash__(self): return hash("x")
    def __eq__(self, other): return other == "x"
keyed_globals = {NamedKey(): 7, 5: 0}
exec("found = x", keyed_globals)
with assert_raises(NameError):
    exec("missing_name", {5: 0})
class KeyedPlain: pass
keyed = KeyedPlain()
keyed.__dict__[NamedKey()] = 8
keyed.__dict__[6] = 0
assert_eq([keyed_globals["found"], keyed.x, hasattr(keyed, "y")], [7, 8, False])
