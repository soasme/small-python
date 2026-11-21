# spec: PLS-315 7.6.2, 23.6
# description: str % a str subclass's instance, or a str subclass's
# instance % one, formats by str's % unless the right operand's class, a
# proper subclass of the left's, has a Python __rmod__; each %s or %r
# calls the instance's Python __str__ or __repr__ once, in order; inside
# comprehensions and generators too.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Str(str):
    def __str__(self):
        for _ in (): pass
        log.append('str'); return "custom"
    def __repr__(self): log.append('repr'); return "R"
class Rm(str):
    def __rmod__(self, o): log.append('rmod'); return 'rm'
    def __str__(self): log.append('s'); return 'S'
class Bad(str):
    def __str__(self): raise KeyError('b')
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
for f in (lambda: "%s" % Str("x"), lambda: "%r|%s" % (Str("x"), Str("y")), lambda: "%s" % Rm("q"), lambda: "%s" % Bad("b"),
          lambda: "%d" % Str("1"), lambda: "a" % Str("x"), lambda: b"%s" % Str("x"), lambda: "%(k)s" % Str("x"),
          lambda: str.__mod__("%s", Str("x")), lambda: Str("%s") % Str("z"), lambda: [("%s" % Str(i)) for i in "ab"]):
    emit(repr(run(f)))
def g(): yield run(lambda: "%s!" % Str("x"))
emit(list(g()))
class Fm(str):
    def __mod__(self, o): log.append('mod'); return 'fm'
class Plain: pass
class Ri:
    def __rmod__(self, o): log.append('ri'); return 'ri'
for f in (lambda: Str("%s|%s") % (Str("a"), 1), lambda: Str("%s") % Rm("w"), lambda: Fm("%s") % Str("x"), lambda: Str("%s") % Plain() != '',
          lambda: Str("%s") % Ri() != "", lambda: Rm("%s") % Str("v")):
    emit(repr(run(f)))
class SubStr(Str):
    def __rmod__(self, o): log.append('sub'); return 'sub'
class StrR(str):
    def __rmod__(self, o): log.append('strr'); return NotImplemented
for f in (lambda: Str("%s") % SubStr("q"), lambda: "%s" % SubStr("q"), lambda: "%s" % StrR("k"), lambda: Str("%s") % StrR("k"), lambda: b"%b" % StrR("k")):
    emit(repr(run(f)))
EXPECTED = [
    "('custom', ['str'])",
    "('R|custom', ['repr', 'str'])",
    "('rm', ['rmod'])",
    '((\'KeyError\', "\'b\'"), [])',
    "(('TypeError', 'format argument: %d requires a real number, not Str'), [])",
    "(('TypeError', 'not all arguments converted during string formatting (required 0, got 1)'), [])",
    "(('TypeError', 'format argument: %b requires a bytes-like object, or an object that implements __bytes__, not Str'), [])",
    "(('TypeError', 'format requires a mapping, not Str'), [])",
    "('custom', ['str'])",
    "('custom', ['str'])",
    "(['custom', 'custom'], ['str', 'str'])",
    "[('custom!', ['str'])]",
    "('custom|1', ['str'])",
    "('S', ['s'])",
    "('fm', ['mod'])",
    '(True, [])',
    '(True, [])',
    "('custom', ['str'])",
    "('sub', ['sub'])",
    "('sub', ['sub'])",
    "('k', ['strr'])",
    "('k', [])",
    "(('TypeError', 'format argument: %b requires a bytes-like object, or an object that implements __bytes__, not StrR'), [])",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
