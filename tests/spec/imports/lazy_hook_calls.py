# spec: PLS-315 17.5, 17.4.4
# description: Reading a lazy import's name in a function, a
# comprehension, a generator or a class body, or calling its resolve(),
# calls the builtins' __import__, a Python hook included, once, which runs
# the module's body; later reads find the bound value, and a body's error
# passes out with an ImportError as its cause.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
import builtins
from log_mod import log
real = builtins.__import__
def hook(name, globals=None, locals=None, fromlist=(), level=0):
    for _ in (): pass
    if name.startswith(('lz_', 'lpk')): log.append(('hook', name, fromlist))
    return real(name, globals, locals, fromlist, level)
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e), type(e.__cause__).__name__)
    return getattr(r, '__name__', r), log[:]
builtins.__import__ = hook
lazy import lz_one
lazy from lpk import sub
lazy import lz_bad
def use(): return lz_one.value, sub.value
emit(run(use))
emit(run(use))
emit(run(lambda: lz_bad))
builtins.__import__ = real
lazy import lz_two
held = [globals()['lz_two']]
emit(run(lambda: held[0].resolve().value))
emit(run(lambda: [lz_two.value for _ in 'ab']))
def g(): yield lz_two.value
emit(run(lambda: list(g())))
class C:
    lazy_value = lz_two.value
emit(run(lambda: C.lazy_value))
EXPECTED = [
    "((5, 8), [('hook', 'lz_one', None), 'lz_one', ('hook', 'lpk', ('sub',)), 'lpk', 'lpk.sub'])",
    '((5, 8), [])',
    "(('LookupError', 'lz', 'ImportError'), [('hook', 'lz_bad', None), 'lz_bad'])",
    "(6, ['lz_two'])",
    '([6, 6], [])',
    '([6], [])',
    '(6, [])',
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
