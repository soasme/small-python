# spec: PLS-315 26.6
# description: reversed() of a mappingproxy, and its __reversed__, read
# the mapping's own __reversed__ attribute, as a Python __getattribute__,
# an instance attribute or a __getattr__ gives it, and call it once,
# returning what it returns; one without it raises AttributeError; inside
# comprehensions and generators too.
from harness import assert_eq
P = type(type.__dict__)
log = []
class M:
    def __getitem__(self, k): return k
    def __iter__(self): return iter("ab")
    def keys(self): return ["a"]
class R(M):
    def __reversed__(self):
        for _ in (): pass
        log.append("rev"); return iter("zy")
class Weird(M):
    def __reversed__(self): log.append("weird"); return 42
class Own(R): pass
class GA(R):
    def __getattribute__(self, n):
        log.append(("ga", n)); return object.__getattribute__(self, n)
class GR(M):
    def __getattr__(self, n):
        log.append(("getattr", n)); return lambda: iter("q")
class Seq(M):
    def __len__(self): return 2
class Raise(M):
    def __reversed__(self): raise KeyError('rv')
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    if type(r).__name__.endswith('iterator'): r = list(r)
    return r, log[:]
o = Own(); o.__reversed__ = lambda: iter("own")
cases = [lambda: reversed(P(R())), lambda: reversed(P(Weird())), lambda: reversed(o), lambda: reversed(P(o)), lambda: reversed(P(GA())),
         lambda: reversed(P(GR())), lambda: reversed(P(Seq())), lambda: reversed(P(Raise())), lambda: reversed(P({"a": 1, "b": 2})),
         lambda: [list(reversed(P(R()))) for _ in (0,)], lambda: P(R()).__reversed__()]
EXPECTED = [
    (['z', 'y'], ['rev']),
    (42, ['weird']),
    (['z', 'y'], ['rev']),
    (['o', 'w', 'n'], []),
    (['z', 'y'], [('ga', '__reversed__'), 'rev']),
    (['q'], [('getattr', '__reversed__')]),
    (('AttributeError', "'Seq' object has no attribute '__reversed__'"), []),
    (('KeyError', "'rv'"), []),
    (['b', 'a'], []),
    ([['z', 'y']], ['rev']),
    (['z', 'y'], ['rev']),
]
assert_eq(len(cases), len(EXPECTED))
for i, (f, expected) in enumerate(zip(cases, EXPECTED)):
    assert_eq(run(f), expected, str(i))
def g(): yield run(cases[0])
assert_eq(list(g()), [EXPECTED[0]])
