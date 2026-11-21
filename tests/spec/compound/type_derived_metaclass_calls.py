# spec: PLS-315 16.4.3, 20.2.2
# description: type(name, bases, ns), and type.__new__(type, ...), whose
# bases' metaclass is more derived with a Python __new__ call that __new__
# with the keywords, the call of type then initializing an instance of
# it by its __init__; the argument checks come first; errors pass out.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class ModelBase(type):
    def __new__(cls, name, bases, attrs, **kw):
        for _ in (): pass
        log.append(('new', cls.__name__, name, kw))
        if name == 'Bad': raise RuntimeWarning(name)
        return super().__new__(cls, name, bases, attrs)
    def __init__(self, name, bases, attrs, **kw):
        log.append(('init', name, kw))
class Model(metaclass=ModelBase): pass
class Other(type):
    def __new__(cls, name, bases, attrs):
        log.append('other'); return 42
Ob = type.__new__(Other, 'Ob', (), {})
class Plain(type):
    def __new__(cls, name, bases, attrs):
        log.append('plain'); return type.__new__(type, name, bases, attrs)
class P(metaclass=Plain): pass
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return (r if isinstance(r, (int, tuple)) else (type(r).__name__, r.__name__)), log[:]
for f in (lambda: type('X', (Model,), {}), lambda: type('Bad', (Model,), {}), lambda: type('K', (Model,), {}, k=1),
          lambda: type(1, (Model,), {}), lambda: type('Y', (P,), {}), lambda: type('Q', (Ob,), {}), lambda: type('Z', (Model, int), {}),
          lambda: ModelBase('W', (Model,), {}), lambda: type.__new__(type, 'V', (Model,), {})):
    emit(run(f))
def g(): yield run(lambda: type('G', (Model,), {}))
emit(list(g()))
EXPECTED = [
    "(('ModelBase', 'X'), [('new', 'ModelBase', 'X', {}), ('init', 'X', {})])",
    "(('RuntimeWarning', 'Bad'), [('new', 'ModelBase', 'Bad', {})])",
    "(('ModelBase', 'K'), [('new', 'ModelBase', 'K', {'k': 1}), ('init', 'K', {'k': 1})])",
    "(('TypeError', 'type.__new__() argument 1 must be str, not int'), [])",
    "(('type', 'Y'), [])",
    "(42, ['other'])",
    "(('ModelBase', 'Z'), [('new', 'ModelBase', 'Z', {}), ('init', 'Z', {})])",
    "(('ModelBase', 'W'), [('new', 'ModelBase', 'W', {}), ('init', 'W', {})])",
    "(('ModelBase', 'V'), [('new', 'ModelBase', 'V', {})])",
    "[(('ModelBase', 'G'), [('new', 'ModelBase', 'G', {}), ('init', 'G', {})])]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
