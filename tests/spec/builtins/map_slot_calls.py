# spec: PLS-315 27.1.6, 26.2
# description: map() of a slot wrapper, unbound or bound to an instance,
# calls it as a call would, so a frozendict or dict subclass's Python
# __missing__ and a str subclass's __str__ under str.__mod__, which may
# loop or raise, run once per item, in order; a builtin's slot over
# builtins maps as before; in a yield from too.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class M(frozendict):
    def __missing__(self, key):
        for _ in (): pass
        log.append(key)
        if key == "bad": raise LookupError("no " + key)
        return ("missing", key)
class D(dict):
    def __missing__(self, key):
        for _ in (): pass
        log.append(("D", key)); return 0
class S(str):
    def __str__(self):
        for _ in (): pass
        log.append("str"); return "custom"
m = M(a=1)
emit(list(map(frozendict.__getitem__, [m, m], [1, 'a'])), log); log.clear()
emit(list(map(m.__getitem__, [2, 'a'])), log); log.clear()
emit(list(map(dict.__getitem__, [D(), D()], [3, 4])), log); log.clear()
emit(list(map(str.__mod__, ["%s", "<%s>"], [S("x"), S("y")])), log); log.clear()
try: list(map(frozendict.__getitem__, [m], ["bad"]))
except LookupError as e: emit("le", e, log); log.clear()
emit(list(map(int.__add__, [1, 2], [3, 4])), list(map(str.__len__, ["ab"])))
def g(): yield from map(frozendict.__getitem__, [m], [5])
emit(list(g()), log)
EXPECTED = [
    "[('missing', 1), 1] [1]",
    "[('missing', 2), 1] [2]",
    "[0, 0] [('D', 3), ('D', 4)]",
    "['custom', '<custom>'] ['str', 'str']",
    "le no bad ['bad']",
    '[4, 6] [2]',
    "[('missing', 5)] [5]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
