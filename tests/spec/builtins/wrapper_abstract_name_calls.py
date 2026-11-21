# spec: PLS-315 20.5.1, 20.6, 20.7
# description: __isabstractmethod__ of a property, staticmethod or
# classmethod reads each function's flag in order and takes its truth,
# a Python __bool__ or __getattr__ included, stopping at the first true
# one; a property's __name__ is its getter's; errors pass out.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Flag:
    def __init__(self, v): self.v = v
    def __bool__(self):
        for _ in (): pass
        log.append(('bool', self.v))
        if self.v is KeyError: raise KeyError('flag')
        return self.v
class Odd:
    def __getattr__(self, name):
        for _ in (): pass
        log.append(name)
        if name == '__isabstractmethod__': return Flag(True)
        if name == '__name__': return 'odd_name'
        raise AttributeError(name)
    def __call__(self, *a): return 1
class Nameless:
    def __getattr__(self, name):
        log.append(name); raise AttributeError(name)
    def __call__(self, *a): return 1
def f(self): pass
def g(self): pass
f.__isabstractmethod__ = Flag(False)
g.__isabstractmethod__ = Flag(KeyError)
def run(x):
    del log[:]
    try: r = x()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
for x in (lambda: property(f).__isabstractmethod__, lambda: property(f, Odd()).__isabstractmethod__,
          lambda: property(g).__isabstractmethod__, lambda: property().__isabstractmethod__,
          lambda: staticmethod(Odd()).__isabstractmethod__, lambda: classmethod(f).__isabstractmethod__,
          lambda: property(Odd()).__name__, lambda: property(Nameless()).__name__, lambda: property(f).__name__,
          lambda: property().__name__, lambda: property(f).__isabstractmethod__(), lambda: dict.__dict__['fromkeys'].__isabstractmethod__,
          lambda: getattr(property(Odd()), '__name__')):
    emit(run(x))
def gen(): yield run(lambda: property(f, Odd()).__isabstractmethod__)
emit(list(gen()))
EXPECTED = [
    "(False, [('bool', False)])",
    "(True, [('bool', False), '__isabstractmethod__', ('bool', True)])",
    '((\'KeyError\', "\'flag\'"), [(\'bool\', <class \'KeyError\'>)])',
    '(False, [])',
    "(True, ['__name__', '__qualname__', '__isabstractmethod__', ('bool', True)])",
    "(False, [('bool', False)])",
    "('odd_name', ['__name__'])",
    '((\'AttributeError\', "\'property\' object has no attribute \'__name__\'"), [\'__name__\'])',
    "('f', [])",
    '((\'AttributeError\', "\'property\' object has no attribute \'__name__\'"), [])',
    '((\'TypeError\', "\'bool\' object is not callable"), [(\'bool\', False)])',
    '((\'AttributeError\', "\'classmethod_descriptor\' object has no attribute \'__isabstractmethod__\'"), [])',
    "('odd_name', ['__name__'])",
    "[(True, [('bool', False), '__isabstractmethod__', ('bool', True)])]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
