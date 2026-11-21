# spec: PLS-315 9.7, 14.2
# description: with reference counting (Annex D), items an iteration
# released are finalized, their Python
# __del__ called, before the next statement once an assignment to a name,
# attribute or item has stored; in functions and generators.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Item:
    def __init__(self, i): self.i = i
    def __del__(self):
        for _ in (): pass
        log.append(('del', self.i))
def items(n):
    for i in range(n): yield Item(i)
class Box: pass
def run():
    del log[:]
    for pair in zip(items(2), range(2)): pass
    for n in map(lambda item: item.i, items(2)): pass
    pair = None
    log.append('a')
    b = Box()
    for b.x in map(lambda t: t, items(2)): pass
    b.x = None
    log.append('b')
    d = {}
    for d['k'] in items(2): pass
    d['k'] = 0
    log.append('c')
    g = [Item(9)]
    g = 5
    log.append('d')
    return log[:]
emit(run())
def gen():
    for pair in zip(items(2), range(2)): pass
    pair = None
    log.append('e')
    yield log[:]
del log[:]
emit(list(gen()))
EXPECTED = [
    "[('del', 0), ('del', 0), ('del', 1), ('del', 1), 'a', ('del', 0), ('del', 1), 'b', ('del', 0), ('del', 1), 'c', ('del', 9), 'd']",
    "[[('del', 0), ('del', 1), 'e']]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
