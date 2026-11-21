# spec: PLS-315 20.5.1
# description: Calling a property subclass reads its getter's Python
# __doc__ once, through property's own __init__ or a Python one calling
# it: the doc, None for an AttributeError, other errors passing out, a
# given doc read never; a subclass with __slots__ cannot store it.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Doc:
    def __init__(self, d): self.d = d
    @property
    def __doc__(self):
        for _ in (): pass
        log.append('doc')
        if self.d is KeyError: raise KeyError('doc')
        if self.d is AttributeError: raise AttributeError
        return self.d
    def __call__(self, s): return 1
class Sub(property): pass
class Slotted(property):
    __slots__ = ()
class Own(property):
    def __init__(self, *a):
        log.append('own'); super().__init__(*a)
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
for f in (lambda: Sub(Doc('text')).__doc__, lambda: Sub(Doc(AttributeError)).__doc__, lambda: Sub(Doc(KeyError)).__doc__,
          lambda: Own(Doc('o')).__doc__, lambda: Slotted(Doc('s')).__doc__, lambda: Slotted(Doc(None)).__doc__,
          lambda: property(Doc('p')).__doc__, lambda: Sub(Doc('x'), None, None, 'given').__doc__,
          lambda: Sub.__init__(property(), Doc('i')), lambda: Sub(Doc(None)).__doc__):
    emit(run(f))
def g(): yield run(lambda: Own(Doc('g')).__doc__)
emit(list(g()))
EXPECTED = [
    "('text', ['doc'])",
    "(None, ['doc'])",
    '((\'KeyError\', "\'doc\'"), [\'doc\'])',
    "('o', ['own', 'doc'])",
    '((\'AttributeError\', "\'Slotted\' object attribute \'__doc__\' is read-only"), [\'doc\'])',
    "(None, ['doc'])",
    "('p', ['doc'])",
    "('given', [])",
    "(None, ['doc'])",
    "(None, ['doc'])",
    "[('g', ['own', 'doc'])]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
