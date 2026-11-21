# spec: PLS-315 19.3.34, 25.1.4
# description: sorted() takes its iterable's items, a generator's or a
# Python __iter__'s, before the sort refuses an unknown keyword; list.sort
# refuses it at once; in a generator too.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
def gen():
    for i in (3, 1, 2):
        log.append(i); yield i
class Items:
    def __iter__(self):
        for _ in (): pass
        log.append('iter'); yield 2; yield 1
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
emit(run(lambda: sorted(gen(), unknown=1)))
emit(run(lambda: sorted(Items(), unknown=1, key=abs)))
emit(run(lambda: sorted(gen(), cmp=None)))
emit(run(lambda: sorted([2, 1], unknown=1)))
emit(run(lambda: sorted(5, unknown=1)))
emit(run(lambda: [3].sort(unknown=1)))
def g(): yield run(lambda: sorted(gen(), bad=2))
emit(list(g()))
EXPECTED = [
    '((\'TypeError\', "sort() got an unexpected keyword argument \'unknown\'"), [3, 1, 2])',
    '((\'TypeError\', "sort() got an unexpected keyword argument \'unknown\'"), [\'iter\'])',
    '((\'TypeError\', "sort() got an unexpected keyword argument \'cmp\'"), [3, 1, 2])',
    '((\'TypeError\', "sort() got an unexpected keyword argument \'unknown\'"), [])',
    '((\'TypeError\', "\'int\' object is not iterable"), [])',
    '((\'TypeError\', "sort() got an unexpected keyword argument \'unknown\'"), [])',
    '[((\'TypeError\', "sort() got an unexpected keyword argument \'bad\'"), [3, 1, 2])]',
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
