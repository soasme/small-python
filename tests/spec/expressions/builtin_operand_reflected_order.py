# spec: PLS-315 7.6.2, 7.6.3, 13.9
# description: A set's or dict's own binary operator, a frozen one's too,
# with an instance of a set's or dict's subclass on the right comes
# before that instance's reflected method unless the instance's class is
# a subclass of the left operand's; then the reflected method comes
# first, and when it returns NotImplemented the builtin's operator still
# applies. A frozenset's or frozendict's |= is its |.
from harness import assert_eq

log = []
def reflected(name):
    def method(self, other):
        for _ in (): pass
        log.append(name)
        return name
    return method
class S(set): pass
class FS(frozenset): pass
class D(dict): pass
class FD(frozendict): pass
for cls in (S, FS, D, FD):
    for name in ('__ror__', '__rand__', '__rsub__', '__rxor__'):
        setattr(cls, name, reflected(name))
class Declined(set):
    def __ror__(self, other):
        log.append('declined'); return NotImplemented
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    if isinstance(r, (set, frozenset)): r = (type(r).__name__, sorted(r))
    return r, log[:]
def ior(x, y):
    x |= y
    return x
CASES = [lambda: frozenset({1}) | S({2}), lambda: frozenset({1}) & S({1}), lambda: frozenset({1}) - S({2}),
         lambda: frozenset({1}) ^ S({2}), lambda: {1} | FS({2}), lambda: {1} | S({2}), lambda: frozenset() | FS(),
         lambda: ior(frozenset({1}), S({2})), lambda: ior({1}, FS({2})), lambda: frozendict(a=1) | D(z=9),
         lambda: {'a': 1} | FD(z=9), lambda: {'a': 1} | D(z=9), lambda: frozendict(a=1) | FD(z=9),
         lambda: ior(frozendict(a=1), D(z=9)), lambda: {1} | Declined({2}), lambda: {1} | D(z=9),
         lambda: {'a': 1} | S({2}), lambda: frozenset({1}).__or__(S({2}))]
EXPECTED = [
    (('frozenset', [1, 2]), []),
    (('frozenset', [1]), []),
    (('frozenset', [1]), []),
    (('frozenset', [1, 2]), []),
    (('set', [1, 2]), []),
    ('__ror__', ['__ror__']),
    ('__ror__', ['__ror__']),
    (('frozenset', [1, 2]), []),
    (('set', [1, 2]), []),
    (frozendict({'a': 1, 'z': 9}), []),
    ({'a': 1, 'z': 9}, []),
    ('__ror__', ['__ror__']),
    ('__ror__', ['__ror__']),
    (frozendict({'a': 1, 'z': 9}), []),
    (('set', [1, 2]), ['declined']),
    ('__ror__', ['__ror__']),
    ('__ror__', ['__ror__']),
    (('frozenset', [1, 2]), []),
]
assert_eq(len(CASES), len(EXPECTED))
for i, (f, expected) in enumerate(zip(CASES, EXPECTED)):
    assert_eq(run(f), expected, str(i))
