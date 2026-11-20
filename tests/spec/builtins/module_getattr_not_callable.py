# spec: PLS-315 7.4.1
# description: calling a module asks its own name's attribute for the
# suggestion through a module __getattr__ that may loop, once: a callable
# value suggests calling it; any other value, and any exception it
# raises, BaseException too, leaves the plain message; inside functions,
# comprehensions and generators too.
from harness import assert_eq
import harness
ModuleType = type(harness)
log = []
def run(f):
    del log[:]
    try: f(); r = 'called'
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def getter(result):
    def g(name):
        for _ in (): pass
        log.append(name)
        if isinstance(result, BaseException): raise result
        return result
    return g
def mod(result):
    m = ModuleType("m"); m.__getattr__ = getter(result); return m
cases = [lambda: mod(print)(), lambda: mod(42)(), lambda: mod(ValueError('v'))(), lambda: mod(AttributeError('a'))(),
         lambda: mod(print)(1, k=2), lambda: [mod(len)() for _ in range(1)], lambda: mod(KeyboardInterrupt())()]
EXPECTED = [
    (('TypeError', "'module' object is not callable. Did you mean: 'm.m(...)'?"), ['m']),
    (('TypeError', "'module' object is not callable"), ['m']),
    (('TypeError', "'module' object is not callable"), ['m']),
    (('TypeError', "'module' object is not callable"), ['m']),
    (('TypeError', "'module' object is not callable. Did you mean: 'm.m(...)'?"), ['m']),
    (('TypeError', "'module' object is not callable. Did you mean: 'm.m(...)'?"), ['m']),
    (('TypeError', "'module' object is not callable"), ['m']),
]
assert_eq(len(cases), len(EXPECTED))
for i, (f, expected) in enumerate(zip(cases, EXPECTED)):
    assert_eq(run(f), expected, str(i))
def inside(): return [run(f) for f in cases]
assert_eq(inside(), EXPECTED)
def g(): yield run(cases[0])
assert_eq(list(g()), [EXPECTED[0]])
