# spec: PLS-315 26.1.1, 26.3.1, 7.7.4
# description: calling a subclass of set, frozenset, list, tuple or dict
# that defines no __new__ or __init__ takes its source as the builtin does:
# a generator's items in turn, each hashed by its Python __hash__ and
# compared by its Python __eq__ before the next is taken, an error from
# either propagating, and gives an instance of the subclass; a dict merged
# into an empty dict, by dict(), a subclass, **, copy(), | or update(),
# compares none of its keys, whose hashes are distinct entries (Annex D),
# while one merged into a full dict compares each stored key of the hash
# with the new one. Inside functions as at module level.
from harness import *

log = []

class K:
    def __init__(self, v): self.v = v
    def __hash__(self):
        for _ in (): pass
        log.append(("h", self.v))
        if self.v == "bad": raise ValueError("hash")
        return 1
    def __eq__(self, other):
        for _ in (): pass
        log.append(("e", self.v, other.v))
        return self.v == other.v
    def __repr__(self): return "K(%r)" % self.v

def gen(*values):
    for v in values:
        log.append(("y", v))
        yield K(v)

class S(set): pass
class F(frozenset): pass
class L(list): pass
class T(tuple): pass
class D(dict): pass
class Mixin: pass
class M(Mixin, set): pass

def builds():
    out = []
    for cls in (S, F, M):
        r = cls(gen(1, 2, 1))
        out.append((type(r).__name__, sorted(k.v for k in r), log[:])); log.clear()
    for cls in (L, T):
        r = cls(gen(1, 2))
        out.append((type(r).__name__, [k.v for k in r], log[:])); log.clear()
    r = D((k, k.v) for k in gen(1, 2, 1))
    out.append((type(r).__name__, sorted(r.values()), log[:])); log.clear()
    r = S([K(1), K(2)])
    out.append((type(r).__name__, len(r), log[:])); log.clear()
    return out

expected = [
    ("S", [1, 2], [("y", 1), ("h", 1), ("y", 2), ("h", 2), ("e", 1, 2), ("y", 1), ("h", 1), ("e", 1, 1)]),
    ("F", [1, 2], [("y", 1), ("h", 1), ("y", 2), ("h", 2), ("e", 1, 2), ("y", 1), ("h", 1), ("e", 1, 1)]),
    ("M", [1, 2], [("y", 1), ("h", 1), ("y", 2), ("h", 2), ("e", 1, 2), ("y", 1), ("h", 1), ("e", 1, 1)]),
    ("L", [1, 2], [("y", 1), ("y", 2)]),
    ("T", [1, 2], [("y", 1), ("y", 2)]),
    ("D", [1, 2], [("y", 1), ("h", 1), ("y", 2), ("h", 2), ("e", 1, 2), ("y", 1), ("h", 1), ("e", 1, 1)]),
    ("S", 2, [("h", 1), ("h", 2), ("e", 1, 2)]),
]
assert_eq(builds(), expected)
log.clear()
r = F(gen(3))
assert_eq((type(r), [k.v for k in r], log), (F, [3], [("y", 3), ("h", 3)]))
log.clear()

# An error from __hash__ propagates from the call; one from the generator too.
def fails():
    out = []
    try: S(gen(1, "bad"))
    except ValueError as e: out.append((e.args, log[:]))
    log.clear()
    def broken():
        yield K(1)
        raise LookupError("gen")
    try: D((k, 0) for k in broken())
    except LookupError as e: out.append((e.args, log[:]))
    log.clear()
    return out

assert_eq(fails(), [(("hash",), [("y", 1), ("h", 1), ("y", "bad"), ("h", "bad")]), (("gen",), [("h", 1)])])

# A class defining __init__, __new__ or __del__ runs it.
class SI(set):
    def __init__(self, source):
        log.append("init")
        super().__init__(source)
class LN(list):
    def __new__(cls, source):
        log.append("new")
        return super().__new__(cls)
def custom():
    a = SI(gen(1)); b = LN(gen(1))
    return (type(a).__name__, len(a), type(b).__name__, list(b), log[:])
r = custom()
assert_eq((r[0], r[1], r[2], [k.v for k in r[3]], r[4]),
          ("SI", 1, "LN", [1], ["init", ("y", 1), ("h", 1), "new", ("y", 1)]))
log.clear()

# A dict merged into an empty one compares no keys; into a full one each
# stored key of the hash compares itself with the new.
def merges():
    d = {K("a"): 1, K("b"): 2, K("c"): 3}
    log.clear()
    sizes = [len(dict(d)), len(D(d)), len({**d}), len(d.copy()), len(d | {})]
    e = {}
    e.update(d)
    sizes.append(len(e))
    quiet = log[:]
    f = {0: 0}
    f.update(d)
    return (sizes, quiet, len(f), [x for x in log if x[0] == "e"])

assert_eq(merges(), ([3, 3, 3, 3, 3, 3], [], 4, [("e", "a", "b"), ("e", "a", "c"), ("e", "b", "c")]))
log.clear()
