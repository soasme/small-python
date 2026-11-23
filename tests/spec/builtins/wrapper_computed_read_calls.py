# spec: PLS-315 20.5.1, 20.6, 20.7, 27.1.4
# description: getattr() and hasattr() of a property's, staticmethod's or
# classmethod's __isabstractmethod__, or a property's __name__, and a
# method call on either, read them as an attribute does: each flag's
# Python __bool__ and a getter's __getattr__, which may loop or raise,
# once and in order; a default or False after an AttributeError; in a
# comprehension and a generator too.
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
        for _ in (): pass
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
for x in (lambda: property(f).__isabstractmethod__(), lambda: property(f, Odd()).__isabstractmethod__(),
          lambda: property(g).__isabstractmethod__(), lambda: property(Odd()).__name__.upper(),
          lambda: property(Nameless()).__name__.upper(), lambda: staticmethod(Odd()).__isabstractmethod__.real,
          lambda: getattr(property(Odd()), '__name__'), lambda: getattr(property(Nameless()), '__name__', 'dflt'),
          lambda: getattr(property(Nameless()), '__name__'), lambda: hasattr(property(Nameless()), '__name__'),
          lambda: hasattr(property(Odd()), '__name__'), lambda: getattr(property(f, Odd()), '__isabstractmethod__'),
          lambda: getattr(classmethod(g), '__isabstractmethod__', 0), lambda: hasattr(staticmethod(g), '__isabstractmethod__'),
          lambda: getattr(property(f), '__doc__'), lambda: [property(Odd()).__name__.lower() for _ in 'ab'],
          lambda: property(f).fget.__name__.upper()):
    emit(run(x))
def gen():
    yield run(lambda: property(f, Odd()).__isabstractmethod__.__class__)
    yield run(lambda: getattr(property(Odd()), '__name__'))
emit(list(gen()))
EXPECTED = [
    '((\'TypeError\', "\'bool\' object is not callable"), [(\'bool\', False)])',
    '((\'TypeError\', "\'bool\' object is not callable"), [(\'bool\', False), \'__isabstractmethod__\', (\'bool\', True)])',
    '((\'KeyError\', "\'flag\'"), [(\'bool\', <class \'KeyError\'>)])',
    "('ODD_NAME', ['__name__'])",
    '((\'AttributeError\', "\'property\' object has no attribute \'__name__\'"), [\'__name__\'])',
    "(1, ['__name__', '__qualname__', '__isabstractmethod__', ('bool', True)])",
    "('odd_name', ['__name__'])",
    "('dflt', ['__name__'])",
    '((\'AttributeError\', "\'property\' object has no attribute \'__name__\'"), [\'__name__\'])',
    "(False, ['__name__'])",
    "(True, ['__name__'])",
    "(True, [('bool', False), '__isabstractmethod__', ('bool', True)])",
    '((\'KeyError\', "\'flag\'"), [(\'bool\', <class \'KeyError\'>)])',
    '((\'KeyError\', "\'flag\'"), [(\'bool\', <class \'KeyError\'>)])',
    '(None, [])',
    "(['odd_name', 'odd_name'], ['__name__', '__name__'])",
    "('F', [])",
    "[(<class 'bool'>, [('bool', False), '__isabstractmethod__', ('bool', True)]), ('odd_name', ['__name__'])]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)

# str.format's field lookup reads the flag too: any of a property's
# functions, or a classmethod's, that is abstract makes it abstract.
def plain(): pass
def marked(): pass
marked.__isabstractmethod__ = True
assert_eq("{0.__isabstractmethod__}|{1.__isabstractmethod__}|{2.__isabstractmethod__}".format(
    property(plain), property(plain, marked), classmethod(marked)), "False|True|True")
