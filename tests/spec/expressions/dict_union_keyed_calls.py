# spec: PLS-315 7.6.2, 7.6.3, 26.1.2, 26.2
# description: A dict's or frozendict's | of an instance of a dict or
# frozendict subclass that overrides __iter__ merges a copy of the left
# operand's items with it by its keys() and __getitem__, in their order,
# the result of the left operand's builtin type; |= updates a dict, or a
# dict subclass's instance, in place, and a frozendict's is its |; errors
# of keys() and __getitem__ propagate, one keeping dict's iteration merges
# its entries, a left operand's own __or__ comes first; and so inside a
# generator.
from harness import assert_eq

log = []
def make(base, mode):
    class K(base):
        def __iter__(self): return iter(())
        def keys(self):
            for _ in (): pass
            log.append('keys')
            if mode == 'keysfail': raise KeyError('k')
            if mode == 'gen': return (k for k in 'bc')
            if mode == 'notiter': return 5
            return ['b', 'a']
        def __getitem__(self, key):
            for _ in (): pass
            log.append(('get', key))
            if mode == 'getfail' and key == 'a': raise IndexError('g')
            return key * 2
    return K
class Kept(dict):
    def keys(self):
        log.append('keys'); return ['x']
class LD(dict): pass
class LF(frozendict): pass
class LO(dict):
    def __or__(self, o):
        for _ in (): pass
        log.append('or'); return 'or'
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def ior(x, y):
    z = x
    x |= y
    return x, x is z
CASES = {}
for base in (dict, frozendict):
    for mode in ('plain', 'keysfail', 'gen', 'notiter', 'getfail', 'empty'):
        K = make(base, mode)
        for left in (dict, frozendict, LD, LF, LO):
            CASES[(base.__name__, mode, left.__name__, '|')] = (lambda K, left, mode: lambda: left(a=1, q=0) | (K() if mode == 'empty' else K(z=9)))(K, left, mode)
            CASES[(base.__name__, mode, left.__name__, '|=')] = (lambda K, left, mode: lambda: ior(left(a=1), K() if mode == 'empty' else K(z=9)))(K, left, mode)
CASES[('kept', '|')] = lambda: {'a': 1} | Kept(x=2)
CASES[('kept', '|=')] = lambda: ior(frozendict(a=1), Kept(x=2))
def g():
    yield {'a': 1} | make(dict, 'plain')(z=1)
    x = frozendict(a=1)
    x |= make(frozendict, 'plain')()
    yield x
    y = LD(a=1)
    y |= make(dict, 'gen')()
    yield y
CASES[('generator',)] = lambda: list(g())
EXPECTED = {
    ('dict', 'plain', 'dict', '|'): ({'a': 'aa', 'q': 0, 'b': 'bb'}, ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'plain', 'dict', '|='): (({'a': 'aa', 'b': 'bb'}, True), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'plain', 'frozendict', '|'): (frozendict({'a': 'aa', 'q': 0, 'b': 'bb'}), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'plain', 'frozendict', '|='): ((frozendict({'a': 'aa', 'b': 'bb'}), False), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'plain', 'LD', '|'): ({'a': 'aa', 'q': 0, 'b': 'bb'}, ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'plain', 'LD', '|='): (({'a': 'aa', 'b': 'bb'}, True), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'plain', 'LF', '|'): (frozendict({'a': 'aa', 'q': 0, 'b': 'bb'}), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'plain', 'LF', '|='): ((frozendict({'a': 'aa', 'b': 'bb'}), False), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'plain', 'LO', '|'): ('or', ['or']),
    ('dict', 'plain', 'LO', '|='): (({'a': 'aa', 'b': 'bb'}, True), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'keysfail', 'dict', '|'): (('KeyError', "'k'"), ['keys']),
    ('dict', 'keysfail', 'dict', '|='): (('KeyError', "'k'"), ['keys']),
    ('dict', 'keysfail', 'frozendict', '|'): (('KeyError', "'k'"), ['keys']),
    ('dict', 'keysfail', 'frozendict', '|='): (('KeyError', "'k'"), ['keys']),
    ('dict', 'keysfail', 'LD', '|'): (('KeyError', "'k'"), ['keys']),
    ('dict', 'keysfail', 'LD', '|='): (('KeyError', "'k'"), ['keys']),
    ('dict', 'keysfail', 'LF', '|'): (('KeyError', "'k'"), ['keys']),
    ('dict', 'keysfail', 'LF', '|='): (('KeyError', "'k'"), ['keys']),
    ('dict', 'keysfail', 'LO', '|'): ('or', ['or']),
    ('dict', 'keysfail', 'LO', '|='): (('KeyError', "'k'"), ['keys']),
    ('dict', 'gen', 'dict', '|'): ({'a': 1, 'q': 0, 'b': 'bb', 'c': 'cc'}, ['keys', ('get', 'b'), ('get', 'c')]),
    ('dict', 'gen', 'dict', '|='): (({'a': 1, 'b': 'bb', 'c': 'cc'}, True), ['keys', ('get', 'b'), ('get', 'c')]),
    ('dict', 'gen', 'frozendict', '|'): (frozendict({'a': 1, 'q': 0, 'b': 'bb', 'c': 'cc'}), ['keys', ('get', 'b'), ('get', 'c')]),
    ('dict', 'gen', 'frozendict', '|='): ((frozendict({'a': 1, 'b': 'bb', 'c': 'cc'}), False), ['keys', ('get', 'b'), ('get', 'c')]),
    ('dict', 'gen', 'LD', '|'): ({'a': 1, 'q': 0, 'b': 'bb', 'c': 'cc'}, ['keys', ('get', 'b'), ('get', 'c')]),
    ('dict', 'gen', 'LD', '|='): (({'a': 1, 'b': 'bb', 'c': 'cc'}, True), ['keys', ('get', 'b'), ('get', 'c')]),
    ('dict', 'gen', 'LF', '|'): (frozendict({'a': 1, 'q': 0, 'b': 'bb', 'c': 'cc'}), ['keys', ('get', 'b'), ('get', 'c')]),
    ('dict', 'gen', 'LF', '|='): ((frozendict({'a': 1, 'b': 'bb', 'c': 'cc'}), False), ['keys', ('get', 'b'), ('get', 'c')]),
    ('dict', 'gen', 'LO', '|'): ('or', ['or']),
    ('dict', 'gen', 'LO', '|='): (({'a': 1, 'b': 'bb', 'c': 'cc'}, True), ['keys', ('get', 'b'), ('get', 'c')]),
    ('dict', 'notiter', 'dict', '|'): (('TypeError', 'make.<locals>.K.keys() must return an iterable, not int'), ['keys']),
    ('dict', 'notiter', 'dict', '|='): (('TypeError', 'make.<locals>.K.keys() must return an iterable, not int'), ['keys']),
    ('dict', 'notiter', 'frozendict', '|'): (('TypeError', 'make.<locals>.K.keys() must return an iterable, not int'), ['keys']),
    ('dict', 'notiter', 'frozendict', '|='): (('TypeError', 'make.<locals>.K.keys() must return an iterable, not int'), ['keys']),
    ('dict', 'notiter', 'LD', '|'): (('TypeError', 'make.<locals>.K.keys() must return an iterable, not int'), ['keys']),
    ('dict', 'notiter', 'LD', '|='): (('TypeError', 'make.<locals>.K.keys() must return an iterable, not int'), ['keys']),
    ('dict', 'notiter', 'LF', '|'): (('TypeError', 'make.<locals>.K.keys() must return an iterable, not int'), ['keys']),
    ('dict', 'notiter', 'LF', '|='): (('TypeError', 'make.<locals>.K.keys() must return an iterable, not int'), ['keys']),
    ('dict', 'notiter', 'LO', '|'): ('or', ['or']),
    ('dict', 'notiter', 'LO', '|='): (('TypeError', 'make.<locals>.K.keys() must return an iterable, not int'), ['keys']),
    ('dict', 'getfail', 'dict', '|'): (('IndexError', 'g'), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'getfail', 'dict', '|='): (('IndexError', 'g'), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'getfail', 'frozendict', '|'): (('IndexError', 'g'), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'getfail', 'frozendict', '|='): (('IndexError', 'g'), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'getfail', 'LD', '|'): (('IndexError', 'g'), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'getfail', 'LD', '|='): (('IndexError', 'g'), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'getfail', 'LF', '|'): (('IndexError', 'g'), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'getfail', 'LF', '|='): (('IndexError', 'g'), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'getfail', 'LO', '|'): ('or', ['or']),
    ('dict', 'getfail', 'LO', '|='): (('IndexError', 'g'), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'empty', 'dict', '|'): ({'a': 'aa', 'q': 0, 'b': 'bb'}, ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'empty', 'dict', '|='): (({'a': 'aa', 'b': 'bb'}, True), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'empty', 'frozendict', '|'): (frozendict({'a': 'aa', 'q': 0, 'b': 'bb'}), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'empty', 'frozendict', '|='): ((frozendict({'a': 'aa', 'b': 'bb'}), False), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'empty', 'LD', '|'): ({'a': 'aa', 'q': 0, 'b': 'bb'}, ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'empty', 'LD', '|='): (({'a': 'aa', 'b': 'bb'}, True), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'empty', 'LF', '|'): (frozendict({'a': 'aa', 'q': 0, 'b': 'bb'}), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'empty', 'LF', '|='): ((frozendict({'a': 'aa', 'b': 'bb'}), False), ['keys', ('get', 'b'), ('get', 'a')]),
    ('dict', 'empty', 'LO', '|'): ('or', ['or']),
    ('dict', 'empty', 'LO', '|='): (({'a': 'aa', 'b': 'bb'}, True), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'plain', 'dict', '|'): ({'a': 'aa', 'q': 0, 'b': 'bb'}, ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'plain', 'dict', '|='): (({'a': 'aa', 'b': 'bb'}, True), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'plain', 'frozendict', '|'): (frozendict({'a': 'aa', 'q': 0, 'b': 'bb'}), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'plain', 'frozendict', '|='): ((frozendict({'a': 'aa', 'b': 'bb'}), False), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'plain', 'LD', '|'): ({'a': 'aa', 'q': 0, 'b': 'bb'}, ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'plain', 'LD', '|='): (({'a': 'aa', 'b': 'bb'}, True), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'plain', 'LF', '|'): (frozendict({'a': 'aa', 'q': 0, 'b': 'bb'}), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'plain', 'LF', '|='): ((frozendict({'a': 'aa', 'b': 'bb'}), False), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'plain', 'LO', '|'): ('or', ['or']),
    ('frozendict', 'plain', 'LO', '|='): (({'a': 'aa', 'b': 'bb'}, True), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'keysfail', 'dict', '|'): (('KeyError', "'k'"), ['keys']),
    ('frozendict', 'keysfail', 'dict', '|='): (('KeyError', "'k'"), ['keys']),
    ('frozendict', 'keysfail', 'frozendict', '|'): (('KeyError', "'k'"), ['keys']),
    ('frozendict', 'keysfail', 'frozendict', '|='): (('KeyError', "'k'"), ['keys']),
    ('frozendict', 'keysfail', 'LD', '|'): (('KeyError', "'k'"), ['keys']),
    ('frozendict', 'keysfail', 'LD', '|='): (('KeyError', "'k'"), ['keys']),
    ('frozendict', 'keysfail', 'LF', '|'): (('KeyError', "'k'"), ['keys']),
    ('frozendict', 'keysfail', 'LF', '|='): (('KeyError', "'k'"), ['keys']),
    ('frozendict', 'keysfail', 'LO', '|'): ('or', ['or']),
    ('frozendict', 'keysfail', 'LO', '|='): (('KeyError', "'k'"), ['keys']),
    ('frozendict', 'gen', 'dict', '|'): ({'a': 1, 'q': 0, 'b': 'bb', 'c': 'cc'}, ['keys', ('get', 'b'), ('get', 'c')]),
    ('frozendict', 'gen', 'dict', '|='): (({'a': 1, 'b': 'bb', 'c': 'cc'}, True), ['keys', ('get', 'b'), ('get', 'c')]),
    ('frozendict', 'gen', 'frozendict', '|'): (frozendict({'a': 1, 'q': 0, 'b': 'bb', 'c': 'cc'}), ['keys', ('get', 'b'), ('get', 'c')]),
    ('frozendict', 'gen', 'frozendict', '|='): ((frozendict({'a': 1, 'b': 'bb', 'c': 'cc'}), False), ['keys', ('get', 'b'), ('get', 'c')]),
    ('frozendict', 'gen', 'LD', '|'): ({'a': 1, 'q': 0, 'b': 'bb', 'c': 'cc'}, ['keys', ('get', 'b'), ('get', 'c')]),
    ('frozendict', 'gen', 'LD', '|='): (({'a': 1, 'b': 'bb', 'c': 'cc'}, True), ['keys', ('get', 'b'), ('get', 'c')]),
    ('frozendict', 'gen', 'LF', '|'): (frozendict({'a': 1, 'q': 0, 'b': 'bb', 'c': 'cc'}), ['keys', ('get', 'b'), ('get', 'c')]),
    ('frozendict', 'gen', 'LF', '|='): ((frozendict({'a': 1, 'b': 'bb', 'c': 'cc'}), False), ['keys', ('get', 'b'), ('get', 'c')]),
    ('frozendict', 'gen', 'LO', '|'): ('or', ['or']),
    ('frozendict', 'gen', 'LO', '|='): (({'a': 1, 'b': 'bb', 'c': 'cc'}, True), ['keys', ('get', 'b'), ('get', 'c')]),
    ('frozendict', 'notiter', 'dict', '|'): (('TypeError', 'make.<locals>.K.keys() must return an iterable, not int'), ['keys']),
    ('frozendict', 'notiter', 'dict', '|='): (('TypeError', 'make.<locals>.K.keys() must return an iterable, not int'), ['keys']),
    ('frozendict', 'notiter', 'frozendict', '|'): (('TypeError', 'make.<locals>.K.keys() must return an iterable, not int'), ['keys']),
    ('frozendict', 'notiter', 'frozendict', '|='): (('TypeError', 'make.<locals>.K.keys() must return an iterable, not int'), ['keys']),
    ('frozendict', 'notiter', 'LD', '|'): (('TypeError', 'make.<locals>.K.keys() must return an iterable, not int'), ['keys']),
    ('frozendict', 'notiter', 'LD', '|='): (('TypeError', 'make.<locals>.K.keys() must return an iterable, not int'), ['keys']),
    ('frozendict', 'notiter', 'LF', '|'): (('TypeError', 'make.<locals>.K.keys() must return an iterable, not int'), ['keys']),
    ('frozendict', 'notiter', 'LF', '|='): (('TypeError', 'make.<locals>.K.keys() must return an iterable, not int'), ['keys']),
    ('frozendict', 'notiter', 'LO', '|'): ('or', ['or']),
    ('frozendict', 'notiter', 'LO', '|='): (('TypeError', 'make.<locals>.K.keys() must return an iterable, not int'), ['keys']),
    ('frozendict', 'getfail', 'dict', '|'): (('IndexError', 'g'), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'getfail', 'dict', '|='): (('IndexError', 'g'), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'getfail', 'frozendict', '|'): (('IndexError', 'g'), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'getfail', 'frozendict', '|='): (('IndexError', 'g'), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'getfail', 'LD', '|'): (('IndexError', 'g'), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'getfail', 'LD', '|='): (('IndexError', 'g'), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'getfail', 'LF', '|'): (('IndexError', 'g'), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'getfail', 'LF', '|='): (('IndexError', 'g'), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'getfail', 'LO', '|'): ('or', ['or']),
    ('frozendict', 'getfail', 'LO', '|='): (('IndexError', 'g'), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'empty', 'dict', '|'): ({'a': 'aa', 'q': 0, 'b': 'bb'}, ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'empty', 'dict', '|='): (({'a': 'aa', 'b': 'bb'}, True), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'empty', 'frozendict', '|'): (frozendict({'a': 'aa', 'q': 0, 'b': 'bb'}), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'empty', 'frozendict', '|='): ((frozendict({'a': 'aa', 'b': 'bb'}), False), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'empty', 'LD', '|'): ({'a': 'aa', 'q': 0, 'b': 'bb'}, ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'empty', 'LD', '|='): (({'a': 'aa', 'b': 'bb'}, True), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'empty', 'LF', '|'): (frozendict({'a': 'aa', 'q': 0, 'b': 'bb'}), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'empty', 'LF', '|='): ((frozendict({'a': 'aa', 'b': 'bb'}), False), ['keys', ('get', 'b'), ('get', 'a')]),
    ('frozendict', 'empty', 'LO', '|'): ('or', ['or']),
    ('frozendict', 'empty', 'LO', '|='): (({'a': 'aa', 'b': 'bb'}, True), ['keys', ('get', 'b'), ('get', 'a')]),
    ('kept', '|'): ({'a': 1, 'x': 2}, []),
    ('kept', '|='): ((frozendict({'a': 1, 'x': 2}), False), []),
    ('generator',): ([{'a': 'aa', 'b': 'bb'}, frozendict({'a': 'aa', 'b': 'bb'}), {'a': 1, 'b': 'bb', 'c': 'cc'}], ['keys', ('get', 'b'), ('get', 'a'), 'keys', ('get', 'b'), ('get', 'a'), 'keys', ('get', 'b'), ('get', 'c')]),
}
assert_eq(len(CASES), len(EXPECTED))
for key, f in CASES.items():
    assert_eq(run(f), EXPECTED[key], repr(key))
