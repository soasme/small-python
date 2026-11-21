# spec: PLS-315 23.6, 7.6.2
# description: str.__mod__ and bytes.__mod__ called by name, given the
# format or bound to it, format as % does: each %s, %r or %c calls the
# argument's Python __str__, __repr__, __bytes__ or __index__, which may
# loop or raise, once and in order, and a str subclass's __rmod__ is not
# called; in a comprehension and a generator too.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class Str(str):
    def __str__(self):
        for _ in (): pass
        log.append('str'); return "custom"
    def __repr__(self):
        for _ in (): pass
        log.append('repr'); return "R"
class Rm(str):
    def __rmod__(self, o): log.append('rmod'); return 'rm'
    def __str__(self):
        for _ in (): pass
        log.append('s'); return 'S'
class Bad(str):
    def __str__(self):
        for _ in (): pass
        raise KeyError('b')
class B:
    def __bytes__(self):
        for _ in (): pass
        log.append('bytes'); return b'BY'
    def __index__(self):
        for _ in (): pass
        log.append('index'); return 65
emit(str.__mod__("%s", Str("x")), log); log.clear()
emit(str.__mod__("%r|%s", (Str("x"), Str("y"))), log); log.clear()
emit(str.__mod__("%s", Rm("q")), log); log.clear()
emit("<%s>".__mod__(Str("b")), log); log.clear()
emit(Str("%s").__mod__(Str("z")), log); log.clear()
try: str.__mod__("%s", Bad("b"))
except KeyError as e: emit("ke", e)
emit(bytes.__mod__(b"%s %c", (B(), B())), log); log.clear()
m = str.__mod__
emit([m("%s", Str(i)) for i in "ab"], log); log.clear()
def g(): yield str.__mod__("%s!", Str("x"))
emit(list(g()), log); log.clear()
emit(str.__mod__("%d", 5), str.__mod__("%(k)s", {"k": Str("v")}), log)
EXPECTED = [
    "custom ['str']",
    "R|custom ['repr', 'str']",
    "S ['s']",
    "<custom> ['str']",
    "custom ['str']",
    "ke 'b'",
    "b'BY A' ['bytes', 'index']",
    "['custom', 'custom'] ['str', 'str']",
    "['custom!'] ['str']",
    "5 custom ['str']",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
