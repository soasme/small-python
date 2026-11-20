# spec: PLS-315 26.1.2, 14.3
# description: A dict's |=, and dict.__ior__ called explicitly, is
# dict.update() of the operand itself: a dict subclass's instance whose
# __iter__ is its own is merged by its keys() and __getitem__, one keeping
# dict's iteration by its entries, whether the left operand is a dict or a
# dict subclass's instance; the left operand is updated in place.
from harness import assert_eq

log = []
class K(dict):
    def __iter__(self): return iter(())
    def keys(self):
        log.append('keys'); return ['b']
    def __getitem__(self, key):
        log.append(('get', key)); return 2
class P(dict):
    def __getitem__(self, key):
        log.append(('get', key)); return 3
class LD(dict): pass
def run(f):
    del log[:]
    r = f()
    return r, log[:]
def ior(x, y):
    z = x
    x |= y
    return x, x is z
CASES = [lambda: ior({'a': 1}, K(z=0)), lambda: ior(LD(a=1), K(z=0)), lambda: ior({'a': 1}, P(z=0)),
         lambda: ior(LD(a=1), P(z=0)), lambda: dict.__ior__({'a': 1}, K(z=0)), lambda: LD(a=1).__ior__(K()),
         lambda: dict.__ior__({}, P(z=0))]
EXPECTED = [
    (({'a': 1, 'b': 2}, True), ['keys', ('get', 'b')]),
    (({'a': 1, 'b': 2}, True), ['keys', ('get', 'b')]),
    (({'a': 1, 'z': 0}, True), []),
    (({'a': 1, 'z': 0}, True), []),
    ({'a': 1, 'b': 2}, ['keys', ('get', 'b')]),
    ({'a': 1, 'b': 2}, ['keys', ('get', 'b')]),
    ({'z': 0}, []),
]
assert_eq(len(CASES), len(EXPECTED))
for i, (f, expected) in enumerate(zip(CASES, EXPECTED)):
    assert_eq(run(f), expected, str(i))
