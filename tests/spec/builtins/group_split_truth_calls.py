# spec: PLS-315 21.4.3, 7.5.1
# description: split() and subgroup() of an exception group take the
# truth of a condition's result as ToBoolean does: a Python __bool__ or
# __len__ runs once per leaf, a non-bool __bool__ result, a negative
# length and their exceptions propagate; inside comprehensions and
# generators too.
from harness import assert_eq
log = []
class Truth:
    def __init__(self, v): self.v = v
    def __bool__(self):
        for _ in (): pass
        log.append(('bool', self.v))
        return self.v
class Sized:
    def __init__(self, n): self.n = n
    def __len__(self):
        for _ in (): pass
        log.append(('len', self.n))
        return self.n
class BadBool:
    def __bool__(self): return 1
class Raises:
    def __bool__(self): raise KeyError('t')
class NegLen:
    def __len__(self): return -1
def tree(): return ExceptionGroup("g", [ValueError(1), KeyError(2), ExceptionGroup("h", [TypeError(3), ValueError(4)])])
def shape(x):
    if x is None: return None
    if isinstance(x, BaseExceptionGroup): return (x.message, [shape(e) for e in x.exceptions])
    return repr(x)
def run(f):
    del log[:]
    try:
        r = f()
        r = [shape(x) for x in r] if isinstance(r, tuple) else shape(r)
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
cases = [lambda: tree().split(lambda e: Truth(isinstance(e, ValueError))), lambda: tree().subgroup(lambda e: Sized(isinstance(e, KeyError))),
         lambda: tree().split(lambda e: BadBool()), lambda: tree().split(lambda e: Raises()), lambda: tree().split(lambda e: NegLen()),
         lambda: tree().split(lambda e: Truth(True)), lambda: tree().subgroup(lambda e: Truth(False)),
         lambda: BaseExceptionGroup.split(tree(), lambda e: Sized(2)), lambda: [tree().split(lambda e: Truth(isinstance(e, TypeError))) for _ in (0,)][0]]
EXPECTED = [
    ([('g', ['ValueError(1)', ('h', ['ValueError(4)'])]), ('g', ['KeyError(2)', ('h', ['TypeError(3)'])])], [('bool', False), ('bool', True), ('bool', False), ('bool', False), ('bool', False), ('bool', True)]),
    (('g', ['KeyError(2)']), [('len', False), ('len', False), ('len', True), ('len', False), ('len', False), ('len', False)]),
    (('TypeError', 'BadBool.__bool__() must return a bool, not int'), []),
    (('KeyError', "'t'"), []),
    (('ValueError', '__len__() should return >= 0'), []),
    ([('g', ['ValueError(1)', 'KeyError(2)', ('h', ['TypeError(3)', 'ValueError(4)'])]), None], [('bool', True)]),
    (None, [('bool', False), ('bool', False), ('bool', False), ('bool', False), ('bool', False), ('bool', False)]),
    ([('g', ['ValueError(1)', 'KeyError(2)', ('h', ['TypeError(3)', 'ValueError(4)'])]), None], [('len', 2)]),
    ([('g', [('h', ['TypeError(3)'])]), ('g', ['ValueError(1)', 'KeyError(2)', ('h', ['ValueError(4)'])])], [('bool', False), ('bool', False), ('bool', False), ('bool', False), ('bool', True), ('bool', False)]),
]
assert_eq(len(cases), len(EXPECTED))
for i, (f, expected) in enumerate(zip(cases, EXPECTED)):
    assert_eq(run(f), expected, str(i))
def g(): yield run(cases[0])
assert_eq(list(g()), [EXPECTED[0]])
