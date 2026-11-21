# spec: PLS-315 7.4.1, 7.3.2
# description: the __call__ wrapper of a function, method or builtin, bound
# or called through its type, a wrapper of a wrapper among them, calls its
# object with the arguments and keywords given; a function's Python code
# runs once, its exceptions and argument errors pass out unchanged; inside
# comprehensions, map() and generators too.
from harness import assert_eq
log = []
def add(a, b=1):
    for _ in (): pass
    log.append((a, b)); return a + b
def boom(): raise KeyError('b')
def gen(): yield 1
class C:
    def m(self, k=0):
        log.append(('m', k)); return k
    def __call__(self, *a): log.append(('call', a)); return a
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    if type(r).__name__ == 'generator': r = list(r)
    return r, log[:]
FT = type(add); MT = type(C().m)
cases = [lambda: add.__call__(1), lambda: add.__call__.__call__(1, b=5), lambda: FT.__call__(add, 2), lambda: len.__call__("abc"),
         lambda: C().m.__call__(k=4), lambda: MT.__call__(C().m, 3), lambda: boom.__call__(), lambda: add.__call__(), lambda: gen.__call__(),
         lambda: FT.__call__(len, 1), lambda: FT.__call__(), lambda: [add.__call__(i) for i in range(2)], lambda: list(map(add.__call__, [5, 6])),
         lambda: C().__call__(1), lambda: add.__call__(*[1, 2]), lambda: add.__call__(**{'a': 3})]
EXPECTED = [
    (2, [(1, 1)]),
    (6, [(1, 5)]),
    (3, [(2, 1)]),
    (3, []),
    (4, [('m', 4)]),
    (3, [('m', 3)]),
    (('KeyError', "'b'"), []),
    (('TypeError', "add() missing 1 required positional argument: 'a'"), []),
    ([1], []),
    (('TypeError', "descriptor '__call__' requires a 'function' object but received a 'builtin_function_or_method'"), []),
    (('TypeError', "descriptor '__call__' of 'function' object needs an argument"), []),
    ([1, 2], [(0, 1), (1, 1)]),
    ([6, 7], [(5, 1), (6, 1)]),
    ((1,), [('call', (1,))]),
    (3, [(1, 2)]),
    (4, [(3, 1)]),
]
assert_eq(len(cases), len(EXPECTED))
for i, (f, expected) in enumerate(zip(cases, EXPECTED)):
    assert_eq(run(f), expected, str(i))
def g(): yield run(cases[0])
assert_eq(list(g()), [EXPECTED[0]])
