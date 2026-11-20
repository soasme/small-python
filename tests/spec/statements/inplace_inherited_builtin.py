# spec: PLS-315 7.6.3, 14.3
# description: The augmented assignment of an instance of a set's, dict's,
# list's or bytearray's subclass whose class defines the plain operator's
# method but not the in-place one takes the in-place method the builtin
# gives it: the instance is updated in place and the Python method is not
# called; a Python in-place method comes first; the plain operator calls
# the Python method; and so inside a generator.
from harness import assert_eq

log = []
class SO(set):
    def __or__(self, o):
        for _ in (): pass
        log.append('or'); return 'or'
    def __and__(self, o):
        for _ in (): pass
        log.append('and'); return 'and'
    __sub__ = __xor__ = __or__
class LA(list):
    def __add__(self, o):
        for _ in (): pass
        log.append('add'); return 'add'
class BA(bytearray):
    def __add__(self, o):
        for _ in (): pass
        log.append('add'); return 'add'
class DO(dict):
    def __or__(self, o):
        for _ in (): pass
        log.append('or'); return 'or'
class Own(dict):
    def __or__(self, o): log.append('or'); return 'or'
    def __ior__(self, o): log.append('ior'); return 'ior'
def run(f):
    del log[:]
    r = f()
    if isinstance(r, (set, frozenset)): r = (type(r).__name__, sorted(r))
    return r, log[:]
def aug(x, op, y):
    z = x
    if op == '|=': x |= y
    elif op == '&=': x &= y
    elif op == '-=': x -= y
    elif op == '^=': x ^= y
    elif op == '+=': x += y
    return sorted(x) if isinstance(x, (set, frozenset)) else x, type(x).__name__, x is z
CASES = [lambda: aug(SO({1}), '|=', {2}), lambda: aug(SO({1, 2}), '&=', {2}), lambda: aug(SO({1, 2}), '-=', {2}),
         lambda: aug(SO({1}), '^=', {2}), lambda: aug(LA([1]), '+=', [2]), lambda: aug(BA(b'a'), '+=', b'b'),
         lambda: aug(DO(a=1), '|=', {'b': 2}), lambda: aug(Own(a=1), '|=', {'b': 2}), lambda: SO({1}) | {2}, lambda: DO() | {}]
def g():
    x = SO({1})
    x |= {2}
    yield sorted(x), type(x).__name__
EXPECTED = [
    (([1, 2], 'SO', True), []),
    (([2], 'SO', True), []),
    (([1], 'SO', True), []),
    (([1, 2], 'SO', True), []),
    (([1, 2], 'LA', True), []),
    ((BA(b'ab'), 'BA', True), []),
    (({'a': 1, 'b': 2}, 'DO', True), []),
    (('ior', 'str', False), ['ior']),
    ('or', ['or']),
    ('or', ['or']),
]
assert_eq(len(CASES), len(EXPECTED))
for i, (f, expected) in enumerate(zip(CASES, EXPECTED)):
    assert_eq(run(f), expected, str(i))
assert_eq(list(g()), [([1, 2], 'SO')])
