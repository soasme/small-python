# spec: PLS-315 27.1.7
# description: A reversed subclass's call reverses a sequence by its
# Python __len__, which may loop, holding the iterator in an instance of
# the subclass that its __init__ initializes; a Python __reversed__'s
# result is the call's value as it is, without __init__; errors and an
# invalid length pass out, through type.__call__ too.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class R(reversed):
    def __length_hint__(self): return 99
class Seq:
    def __len__(self):
        for _ in (): pass
        log.append("len"); return 2
    def __getitem__(self, i): return "ab"[i]
r = R(Seq())
emit(type(r) is R, r.__length_hint__(), list(r), log)
class Own:
    def __reversed__(self):
        for _ in (): pass
        log.append("rev"); return iter([3, 2])
log.clear(); o = R(Own()); emit(type(o).__name__, list(o), log)
class Odd:
    def __reversed__(self):
        for _ in (): pass
        return Odd
log.clear(); emit(R(Odd()))
class Init(reversed):
    def __init__(self, seq):
        for _ in (): pass
        log.append(("init", type(seq).__name__))
log.clear(); i = Init(Seq()); emit(type(i).__name__, log)
emit(list(i))
log.clear(); i = Init(Own()); emit(type(i).__name__, list(i), log)
class BadLen:
    def __len__(self):
        for _ in (): pass
        raise KeyError("len")
    def __getitem__(self, i): return i
try: R(BadLen())
except KeyError as e: emit("ke", e)
class Neg:
    def __len__(self):
        for _ in (): pass
        return -1
    def __getitem__(self, i): return i
try: R(Neg())
except ValueError as e: emit("ve", e)
emit(list(type.__call__(R, Seq())), list(reversed(Seq())))
class D(dict):
    def __len__(self): return 3
try: R(D())
except TypeError as e: emit("te", e)
EXPECTED = [
    "True 99 ['b', 'a'] ['len']",
    "list_iterator [3, 2] ['rev']",
    "<class '__main__.Odd'>",
    "Init ['len', ('init', 'Seq')]",
    "['b', 'a']",
    "list_iterator [3, 2] ['rev']",
    "ke 'len'",
    've __len__() should return >= 0',
    "['b', 'a'] ['b', 'a']",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
