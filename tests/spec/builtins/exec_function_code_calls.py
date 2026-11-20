# spec: PLS-315 19.3.14, 19.3.15
# description: eval() and exec() of a function's code call it with no
# arguments in the given globals, eval() giving its value and exec() None;
# its exception propagates, a generator function's code gives a
# generator, a closure's cells are its free variables; inside functions,
# comprehensions and generators too.
from harness import assert_eq

log = []
def five():
    for _ in (): pass
    log.append('five'); return 5
def bad():
    for _ in (): pass
    raise KeyError('b')
def gen():
    yield 1
def outer():
    x = 1
    def inner():
        for _ in (): pass
        return x
    return inner
cell = outer().__closure__
def g(): pass
def uses_global():
    for _ in (): pass
    return G
def run(f):
    del log[:]
    try: r = f()
    except BaseException as e: r = (type(e).__name__, str(e))
    if type(r).__name__ == 'generator': r = 'generator'
    return r, log[:]
cases = [lambda: eval(five.__code__), lambda: exec(five.__code__), lambda: eval(bad.__code__), lambda: exec(bad.__code__),
         lambda: eval(gen.__code__), lambda: exec(gen.__code__), lambda: exec(outer().__code__, None, None, closure=cell),
         lambda: exec(outer().__code__, {}, closure=cell), lambda: eval(uses_global.__code__, {'G': 7}),
         lambda: eval(uses_global.__code__, {}), lambda: exec(five.__code__, {}, {}),
         lambda: [eval(five.__code__) for _ in range(2)], lambda: eval(outer().__code__)]
EXPECTED = [
    (5, ['five']),
    (None, ['five']),
    (('KeyError', "'b'"), []),
    (('KeyError', "'b'"), []),
    ('generator', []),
    (None, []),
    (None, []),
    (None, []),
    (7, []),
    (('NameError', "name 'G' is not defined"), []),
    (('NameError', "name 'log' is not defined"), []),
    ([5, 5], ['five', 'five']),
    (('TypeError', 'code object passed to eval() may not contain free variables'), []),
]
assert_eq(len(cases), len(EXPECTED))
for i, (f, expected) in enumerate(zip(cases, EXPECTED)):
    assert_eq(run(f), expected, str(i))
def inside():
    return [run(f) for f in cases]
assert_eq(inside(), EXPECTED)
def gg():
    yield eval(five.__code__)
assert_eq(list(gg()), [5])
