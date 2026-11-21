# spec: PLS-315 7.3.4, 7.3.2
# description: a __getattribute__ that is a descriptor, of a class or a
# metaclass, is bound by its Python __get__ and called on the name, for
# reads, getattr() and hasattr(); its AttributeError then binds and calls
# __getattr__, a descriptor too, even the same one; other errors pass out.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Bind:
    def __get__(s, obj, owner):
        for _ in (): pass
        log.append(('get', type(obj).__name__, owner.__name__))
        def look(name):
            log.append(('look', name))
            if name.startswith('miss'): raise AttributeError(name)
            if name == 'bad': raise ValueError(name)
            return (name, owner.__name__)
        return look
class Special:
    __getattribute__ = Bind()
class Fallback(Special):
    def __getattr__(s, name): log.append(('fallback', name)); return 'fb'
def t(f):
    try: return f()
    except Exception as e: return (type(e).__name__, str(e))
for cls in (Special, Fallback):
    for name in ('custom', 'missing', 'bad'):
        log.clear()
        emit(t(lambda: getattr(cls(), name)), t(lambda: getattr(cls(), name, 'dflt')), t(lambda: hasattr(cls(), name)), log)
log.clear(); o = Fallback(); emit(o.custom, o.missing, t(lambda: o.bad), log)
log.clear(); emit(t(lambda: Special().custom), t(lambda: Special().missing), log)
class Meta(type):
    __getattribute__ = Bind()
class K(metaclass=Meta): pass
log.clear(); emit(t(lambda: K.attr), log)
class P:
    __getattribute__ = property(lambda s: (lambda n: ('prop', n)))
emit(P().x, getattr(P(), 'y'))
d = Bind()
class Both:
    __getattribute__ = d
    __getattr__ = d
log.clear(); emit(t(lambda: Both().missing), Both().here, log)
EXPECTED = [
    "('custom', 'Special') ('custom', 'Special') True [('get', 'Special', 'Special'), ('look', 'custom'), ('get', 'Special', 'Special'), ('look', 'custom'), ('get', 'Special', 'Special'), ('look', 'custom')]",
    "('AttributeError', 'missing') dflt False [('get', 'Special', 'Special'), ('look', 'missing'), ('get', 'Special', 'Special'), ('look', 'missing'), ('get', 'Special', 'Special'), ('look', 'missing')]",
    "('ValueError', 'bad') ('ValueError', 'bad') ('ValueError', 'bad') [('get', 'Special', 'Special'), ('look', 'bad'), ('get', 'Special', 'Special'), ('look', 'bad'), ('get', 'Special', 'Special'), ('look', 'bad')]",
    "('custom', 'Fallback') ('custom', 'Fallback') True [('get', 'Fallback', 'Fallback'), ('look', 'custom'), ('get', 'Fallback', 'Fallback'), ('look', 'custom'), ('get', 'Fallback', 'Fallback'), ('look', 'custom')]",
    "fb fb True [('get', 'Fallback', 'Fallback'), ('look', 'missing'), ('fallback', 'missing'), ('get', 'Fallback', 'Fallback'), ('look', 'missing'), ('fallback', 'missing'), ('get', 'Fallback', 'Fallback'), ('look', 'missing'), ('fallback', 'missing')]",
    "('ValueError', 'bad') ('ValueError', 'bad') ('ValueError', 'bad') [('get', 'Fallback', 'Fallback'), ('look', 'bad'), ('get', 'Fallback', 'Fallback'), ('look', 'bad'), ('get', 'Fallback', 'Fallback'), ('look', 'bad')]",
    "('custom', 'Fallback') fb ('ValueError', 'bad') [('get', 'Fallback', 'Fallback'), ('look', 'custom'), ('get', 'Fallback', 'Fallback'), ('look', 'missing'), ('fallback', 'missing'), ('get', 'Fallback', 'Fallback'), ('look', 'bad')]",
    "('custom', 'Special') ('AttributeError', 'missing') [('get', 'Special', 'Special'), ('look', 'custom'), ('get', 'Special', 'Special'), ('look', 'missing')]",
    "('attr', 'Meta') [('get', 'Meta', 'Meta'), ('look', 'attr')]",
    "('prop', 'x') ('prop', 'y')",
    "('AttributeError', 'missing') ('here', 'Both') [('get', 'Both', 'Both'), ('look', 'missing'), ('get', 'Both', 'Both'), ('look', 'missing'), ('get', 'Both', 'Both'), ('look', 'here')]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
