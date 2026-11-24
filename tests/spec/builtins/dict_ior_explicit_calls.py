# spec: PLS-315 26.1.2, 14.3
# description: dict.__ior__ called explicitly, given a dict or a dict
# subclass's instance or bound to it, merges a mapping's Python keys() and
# __getitem__, which may loop or raise, or pairs, into that dict as its |=
# does, returning the dict itself; a subclass's own __ior__ is not called.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
class K(dict):
    def __iter__(self): return iter(())
    def keys(self):
        for _ in (): pass
        log.append('keys'); return ['b', 'c']
    def __getitem__(self, key):
        for _ in (): pass
        log.append(('get', key)); return key * 2
class P:
    def keys(self):
        for _ in (): pass
        log.append('pk'); return ['p']
    def __getitem__(self, key):
        for _ in (): pass
        if key == 'bad': raise KeyError(key)
        return 9
class Bad:
    def keys(self):
        for _ in (): pass
        return ['bad']
    __getitem__ = P.__getitem__
class LD(dict): pass
class Own(dict):
    def __ior__(self, other): return "own"
d = {'a': 1}
r = dict.__ior__(d, K(z=0))
emit(r, r is d, log); log.clear()
e = LD(a=1); r = e.__ior__(K())
emit(r, r is e, type(r).__name__, log); log.clear()
o = Own(a=1); emit(dict.__ior__(o, P()), o.__ior__(P()), log); log.clear()
f = dict.__ior__
emit(f({}, P()), log); log.clear()
try: dict.__ior__({}, Bad())
except KeyError as ex: emit("ke", ex)
emit(dict.__ior__({}, [("x", 1)]), {}.__ior__(K()), log); log.clear()
def g(): return dict.__ior__({1: 2}, K())
emit(g(), log)
EXPECTED = [
    "{'a': 1, 'b': 'bb', 'c': 'cc'} True ['keys', ('get', 'b'), ('get', 'c')]",
    "{'a': 1, 'b': 'bb', 'c': 'cc'} True LD ['keys', ('get', 'b'), ('get', 'c')]",
    "{'a': 1, 'p': 9} own ['pk']",
    "{'p': 9} ['pk']",
    "ke 'bad'",
    "{'x': 1} {'b': 'bb', 'c': 'cc'} ['keys', ('get', 'b'), ('get', 'c')]",
    "{1: 2, 'b': 'bb', 'c': 'cc'} ['keys', ('get', 'b'), ('get', 'c')]",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
# Unbound with its dict, bound, or the bound method held, and a dict of
# Python-hashed keys, whose stored hashes it reuses.
ior_log = []
class IorMapping:
    def keys(self):
        for _ in (): pass
        ior_log.append("keys"); return ["a"]
    def __getitem__(self, k):
        for _ in (): pass
        ior_log.append(("get", k)); return 1
class IorKey:
    def __hash__(self):
        for _ in (): pass
        ior_log.append("hash"); return 1
    def __eq__(self, o): return self is o
def explicit_forms():
    d, m = {}, IorMapping()
    r1 = dict.__ior__(d, m)
    e, p = {}, {IorKey(): 2}
    r2 = e.__ior__(p)
    f = {}; ior = f.__ior__
    r3 = ior(m)
    return r1 is d, sorted(d.items()), r2 is e, len(e), r3 is f, ior_log
assert_eq(explicit_forms(), (True, [("a", 1)], True, 1, True, ["keys", ("get", "a"), "hash", "keys", ("get", "a")]))
