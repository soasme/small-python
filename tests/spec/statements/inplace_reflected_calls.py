# spec: PLS-315 7.6.3, 14.3
# description: an augmented assignment to a list or bytearray subclass by
# * calls the right operand's Python reflected method before the inherited
# repetition, and a set subclass's inherited in-place operator declines an
# instance so that its reflected method is called; inside functions,
# comprehensions and generators too.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Reflected:
    def __radd__(self, o):
        for _ in (): pass
        log.append('radd'); return "radd"
    def __rmul__(self, o):
        for _ in (): pass
        log.append('rmul'); return "rmul"
    def __rsub__(self, o):
        for _ in (): pass
        log.append('rsub'); return type(o)
    def __ror__(self, o): log.append('ror'); return type(o)
class Declines:
    def __rmul__(self, o):
        for _ in (): pass
        log.append('decl'); return NotImplemented
    def __index__(self): log.append('idx'); return 2
class SubList(list): pass
class SubBA(bytearray): pass
class OwnMul(list):
    def __imul__(self, o): log.append('own'); return 'own'
class SubSet(set): pass
class SubDict(dict): pass
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def aug(x, y, op):
    for _ in (): pass
    if op == '*': x *= y
    elif op == '+': x += y
    elif op == '-': x -= y
    else: x |= y
    return x
for x, y, op in ((SubList([1]), Reflected(), '*'), (SubList([1]), Reflected(), '+'), (SubBA(b'a'), Reflected(), '*'), (SubList([1]), Declines(), '*'),
                 (OwnMul([1]), Reflected(), '*'), (SubList([1]), Reflected(), '-'), (SubSet({1}), Reflected(), '|'), (SubDict(), Reflected(), '|'),
                 ([1], Reflected(), '*'), (SubList([1]), 2, '*'), (SubBA(b'a'), Declines(), '*')):
    emit(repr(run(lambda: aug(x, y, op))))
x = SubList([1]); x *= Reflected(); emit(x, log)
def g():
    x = SubList([1]); x *= Reflected(); yield x
emit(list(g()))
class SubFS(frozenset): pass
class Both:
    def __ror__(self, o):
        for _ in (): pass
        log.append('both'); return NotImplemented
for x, y, op in ((SubSet({1}), Both(), '|'), (SubSet({1}), {2}, '|'), (SubDict(a=1), {'b': 2}, '|'), (SubFS({1}), Reflected(), '|'),
                 (SubSet({1}), SubSet({3}), '|'), (SubSet({1}), Reflected(), '-')):
    emit(repr(run(lambda: aug(x, y, op))))
EXPECTED = [
    "('rmul', ['rmul'])",
    '((\'TypeError\', "\'Reflected\' object is not iterable"), [])',
    "('rmul', ['rmul'])",
    "([1, 1], ['decl', 'idx'])",
    "('own', ['own'])",
    "(<class '__main__.SubList'>, ['rsub'])",
    "(<class '__main__.SubSet'>, ['ror'])",
    '((\'TypeError\', "\'Reflected\' object is not iterable"), [])',
    "('rmul', ['rmul'])",
    '([1, 1], [])',
    "(SubBA(b'aa'), ['decl', 'idx'])",
    "rmul ['decl', 'idx', 'rmul']",
    "['rmul']",
    '((\'TypeError\', "unsupported operand type(s) for |=: \'SubSet\' and \'Both\'"), [\'both\'])',
    '(SubSet({1, 2}), [])',
    "({'a': 1, 'b': 2}, [])",
    "(<class '__main__.SubFS'>, ['ror'])",
    '(SubSet({1, 3}), [])',
    "(<class '__main__.SubSet'>, ['rsub'])",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
