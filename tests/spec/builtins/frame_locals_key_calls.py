# spec: PLS-315 28.3, 26.5, 13.10.1
# description: A FrameLocalsProxy's subscript, store, in and not in, and
# its __getitem__, __contains__ and __setitem__ called explicitly, hash a
# key that is no exact str by its Python __hash__ and compare it with each
# local variable's name of that hash by its Python __eq__, in order, the
# name it equals standing for the variable; their exceptions propagate,
# also inside a comprehension and a suspended generator.
from harness import *

log = []
class K:
    def __init__(self, name, h=None, eq=None):
        self.name, self.h, self.eq = name, h, eq
    def __repr__(self):
        return f"K({self.name})"
    def __hash__(self):
        for _ in (): pass
        log.append(("hash", self.name))
        if self.h == "raise": raise KeyError("h")
        if self.h == "bad": return "no"
        return hash(self.name)
    def __eq__(self, other):
        for _ in (): pass
        log.append(("eq", self.name, repr(other)))
        if self.eq == "raise": raise KeyError("e")
        if self.eq == "list": return [1] if other == self.name else []
        return other == self.name
class S(str):
    def __eq__(self, other):
        for _ in (): pass
        log.append(("S.eq", str(self), repr(other)))
        return str.__eq__(self, other)
    __hash__ = str.__hash__
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, list(log)
def current():
    try:
        raise ValueError
    except ValueError as e:
        return e.__traceback__.tb_frame.f_back
def body():
    x = 1
    y = 2
    p = current().f_locals
    def store(k, v):
        p[k] = v
        return x, y
    def delete(k):
        del p[k]
    def gen():
        yield p[K("x")]
        yield K("y") in p
    k = K("x")
    assert_eq(run(lambda: p[k]), (1, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: k in p), (True, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: k not in p), (False, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: 1 if k in p else 0), (1, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: k in p in [p]), (True, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: p.__getitem__(k)), (1, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: p.__contains__(k)), (True, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: p.get(k)), (1, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: p.get(k, "d")), (1, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: p.setdefault(k, 7)), (1, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: p.pop(k, "none")), (('ValueError', 'cannot remove local variables from FrameLocalsProxy'), [('hash', 'x'), ('eq', 'x', "'x'")]))
    k = K("y")
    assert_eq(run(lambda: p[k]), (2, [('hash', 'y'), ('eq', 'y', "'y'")]))
    assert_eq(run(lambda: k in p), (True, [('hash', 'y'), ('eq', 'y', "'y'")]))
    assert_eq(run(lambda: k not in p), (False, [('hash', 'y'), ('eq', 'y', "'y'")]))
    assert_eq(run(lambda: 1 if k in p else 0), (1, [('hash', 'y'), ('eq', 'y', "'y'")]))
    assert_eq(run(lambda: k in p in [p]), (True, [('hash', 'y'), ('eq', 'y', "'y'")]))
    assert_eq(run(lambda: p.__getitem__(k)), (2, [('hash', 'y'), ('eq', 'y', "'y'")]))
    assert_eq(run(lambda: p.__contains__(k)), (True, [('hash', 'y'), ('eq', 'y', "'y'")]))
    assert_eq(run(lambda: p.get(k)), (2, [('hash', 'y'), ('eq', 'y', "'y'")]))
    assert_eq(run(lambda: p.get(k, "d")), (2, [('hash', 'y'), ('eq', 'y', "'y'")]))
    assert_eq(run(lambda: p.setdefault(k, 7)), (2, [('hash', 'y'), ('eq', 'y', "'y'")]))
    assert_eq(run(lambda: p.pop(k, "none")), (('ValueError', 'cannot remove local variables from FrameLocalsProxy'), [('hash', 'y'), ('eq', 'y', "'y'")]))
    k = K("zz")
    assert_eq(run(lambda: p[k]), (('KeyError', '"local variable \'K(zz)\' is not defined"'), [('hash', 'zz')]))
    assert_eq(run(lambda: k in p), (False, [('hash', 'zz')]))
    assert_eq(run(lambda: k not in p), (True, [('hash', 'zz')]))
    assert_eq(run(lambda: 1 if k in p else 0), (0, [('hash', 'zz')]))
    assert_eq(run(lambda: k in p in [p]), (False, [('hash', 'zz')]))
    assert_eq(run(lambda: p.__getitem__(k)), (('KeyError', '"local variable \'K(zz)\' is not defined"'), [('hash', 'zz')]))
    assert_eq(run(lambda: p.__contains__(k)), (False, [('hash', 'zz')]))
    assert_eq(run(lambda: p.get(k)), (None, [('hash', 'zz')]))
    assert_eq(run(lambda: p.get(k, "d")), ('d', [('hash', 'zz')]))
    assert_eq(run(lambda: p.setdefault(k, 7)), (7, [('hash', 'zz'), ('hash', 'zz'), ('hash', 'zz')]))
    assert_eq(run(lambda: p.pop(k, "none")), (7, [('hash', 'zz'), ('hash', 'zz')]))
    k = K("x", h="raise")
    assert_eq(run(lambda: p[k]), (('KeyError', "'h'"), [('hash', 'x')]))
    assert_eq(run(lambda: k in p), (('KeyError', "'h'"), [('hash', 'x')]))
    assert_eq(run(lambda: k not in p), (('KeyError', "'h'"), [('hash', 'x')]))
    assert_eq(run(lambda: 1 if k in p else 0), (('KeyError', "'h'"), [('hash', 'x')]))
    assert_eq(run(lambda: k in p in [p]), (('KeyError', "'h'"), [('hash', 'x')]))
    assert_eq(run(lambda: p.__getitem__(k)), (('KeyError', "'h'"), [('hash', 'x')]))
    assert_eq(run(lambda: p.__contains__(k)), (('KeyError', "'h'"), [('hash', 'x')]))
    assert_eq(run(lambda: p.get(k)), (None, [('hash', 'x')]))
    assert_eq(run(lambda: p.get(k, "d")), ('d', [('hash', 'x')]))
    assert_eq(run(lambda: p.setdefault(k, 7)), (('KeyError', "'h'"), [('hash', 'x'), ('hash', 'x')]))
    assert_eq(run(lambda: p.pop(k, "none")), (('KeyError', "'h'"), [('hash', 'x')]))
    k = K("x", h="bad")
    assert_eq(run(lambda: p[k]), (('TypeError', '__hash__ method should return an integer'), [('hash', 'x')]))
    assert_eq(run(lambda: k in p), (('TypeError', '__hash__ method should return an integer'), [('hash', 'x')]))
    assert_eq(run(lambda: k not in p), (('TypeError', '__hash__ method should return an integer'), [('hash', 'x')]))
    assert_eq(run(lambda: 1 if k in p else 0), (('TypeError', '__hash__ method should return an integer'), [('hash', 'x')]))
    assert_eq(run(lambda: k in p in [p]), (('TypeError', '__hash__ method should return an integer'), [('hash', 'x')]))
    assert_eq(run(lambda: p.__getitem__(k)), (('TypeError', '__hash__ method should return an integer'), [('hash', 'x')]))
    assert_eq(run(lambda: p.__contains__(k)), (('TypeError', '__hash__ method should return an integer'), [('hash', 'x')]))
    assert_eq(run(lambda: p.get(k)), (('TypeError', '__hash__ method should return an integer'), [('hash', 'x')]))
    assert_eq(run(lambda: p.get(k, "d")), (('TypeError', '__hash__ method should return an integer'), [('hash', 'x')]))
    assert_eq(run(lambda: p.setdefault(k, 7)), (('TypeError', '__hash__ method should return an integer'), [('hash', 'x')]))
    assert_eq(run(lambda: p.pop(k, "none")), (('TypeError', '__hash__ method should return an integer'), [('hash', 'x')]))
    k = K("x", eq="raise")
    assert_eq(run(lambda: p[k]), (('KeyError', "'e'"), [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: k in p), (('KeyError', "'e'"), [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: k not in p), (('KeyError', "'e'"), [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: 1 if k in p else 0), (('KeyError', "'e'"), [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: k in p in [p]), (('KeyError', "'e'"), [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: p.__getitem__(k)), (('KeyError', "'e'"), [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: p.__contains__(k)), (('KeyError', "'e'"), [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: p.get(k)), (None, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: p.get(k, "d")), ('d', [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: p.setdefault(k, 7)), (('KeyError', "'e'"), [('hash', 'x'), ('eq', 'x', "'x'"), ('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: p.pop(k, "none")), (('KeyError', "'e'"), [('hash', 'x'), ('eq', 'x', "'x'")]))
    k = K("x", eq="list")
    assert_eq(run(lambda: p[k]), (1, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: k in p), (True, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: k not in p), (False, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: 1 if k in p else 0), (1, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: k in p in [p]), (True, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: p.__getitem__(k)), (1, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: p.__contains__(k)), (True, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: p.get(k)), (1, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: p.get(k, "d")), (1, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: p.setdefault(k, 7)), (1, [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: p.pop(k, "none")), (('ValueError', 'cannot remove local variables from FrameLocalsProxy'), [('hash', 'x'), ('eq', 'x', "'x'")]))
    k = S("y")
    assert_eq(run(lambda: p[k]), (2, [('S.eq', 'y', "'y'")]))
    assert_eq(run(lambda: k in p), (True, [('S.eq', 'y', "'y'")]))
    assert_eq(run(lambda: k not in p), (False, [('S.eq', 'y', "'y'")]))
    assert_eq(run(lambda: 1 if k in p else 0), (1, [('S.eq', 'y', "'y'")]))
    assert_eq(run(lambda: k in p in [p]), (True, [('S.eq', 'y', "'y'")]))
    assert_eq(run(lambda: p.__getitem__(k)), (2, [('S.eq', 'y', "'y'")]))
    assert_eq(run(lambda: p.__contains__(k)), (True, [('S.eq', 'y', "'y'")]))
    assert_eq(run(lambda: p.get(k)), (2, [('S.eq', 'y', "'y'")]))
    assert_eq(run(lambda: p.get(k, "d")), (2, [('S.eq', 'y', "'y'")]))
    assert_eq(run(lambda: p.setdefault(k, 7)), (2, [('S.eq', 'y', "'y'")]))
    assert_eq(run(lambda: p.pop(k, "none")), (('ValueError', 'cannot remove local variables from FrameLocalsProxy'), [('S.eq', 'y', "'y'")]))
    assert_eq(run(lambda: store(K("x"), 10)), ((10, 2), [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: store(K("y", eq="raise"), 11)), (('KeyError', "'e'"), [('hash', 'y'), ('eq', 'y', "'y'")]))
    assert_eq(run(lambda: store(K("new"), 12)), ((10, 2), [('hash', 'new'), ('hash', 'new')]))
    assert_eq(run(lambda: (p.__setitem__(K("y"), 13), y)), ((None, 13), [('hash', 'y'), ('eq', 'y', "'y'")]))
    assert_eq(run(lambda: [p[K("x")] for _ in range(2)]), ([10, 10], [('hash', 'x'), ('eq', 'x', "'x'"), ('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: list(gen())), ([10, True], [('hash', 'x'), ('eq', 'x', "'x'"), ('hash', 'y'), ('eq', 'y', "'y'")]))
    assert_eq(run(lambda: p[K("new")]), (12, [('hash', 'new'), ('hash', 'new'), ('eq', 'new', 'K(new)'), ('eq', 'new', "'new'")]))
    assert_eq(run(lambda: K("new") in p), (True, [('hash', 'new'), ('hash', 'new'), ('eq', 'new', 'K(new)'), ('eq', 'new', "'new'")]))
    assert_eq(run(lambda: K("zz") not in p), (True, [('hash', 'zz'), ('hash', 'zz')]))
    assert_eq(run(lambda: p.get(K("new"))), (12, [('hash', 'new'), ('hash', 'new'), ('eq', 'new', 'K(new)'), ('eq', 'new', "'new'")]))
    assert_eq(run(lambda: p.get(K("zz"), "d")), ('d', [('hash', 'zz'), ('hash', 'zz')]))
    assert_eq(run(lambda: p.__contains__(K("new"))), (True, [('hash', 'new'), ('hash', 'new'), ('eq', 'new', 'K(new)'), ('eq', 'new', "'new'")]))
    assert_eq(run(lambda: p.setdefault(K("new"), 0)), (12, [('hash', 'new'), ('hash', 'new'), ('eq', 'new', 'K(new)'), ('eq', 'new', "'new'")]))
    assert_eq(run(lambda: p.setdefault(K("other"), 14)), (14, [('hash', 'other'), ('hash', 'other'), ('hash', 'other'), ('hash', 'other')]))
    assert_eq(run(lambda: p[K("other")]), (14, [('hash', 'other'), ('hash', 'other'), ('eq', 'other', 'K(other)'), ('eq', 'other', "'other'")]))
    assert_eq(run(lambda: p[K("zz")]), (('KeyError', '"local variable \'K(zz)\' is not defined"'), [('hash', 'zz'), ('hash', 'zz')]))
    assert_eq(run(lambda: store(K("new"), 15)), ((10, 13), [('hash', 'new'), ('hash', 'new'), ('eq', 'new', 'K(new)'), ('eq', 'new', "'new'")]))
    assert_eq(run(lambda: p[K("new")]), (15, [('hash', 'new'), ('hash', 'new'), ('eq', 'new', 'K(new)'), ('eq', 'new', "'new'")]))
    assert_eq(run(lambda: p[K("new", eq="raise")]), (('KeyError', "'e'"), [('hash', 'new'), ('hash', 'new'), ('eq', 'new', 'K(new)'), ('eq', 'new', "'new'")]))
    assert_eq(run(lambda: p.get(K("new", h="raise"))), (None, [('hash', 'new')]))
    assert_eq(run(lambda: delete(K("new"))), (None, [('hash', 'new'), ('hash', 'new'), ('eq', 'new', 'K(new)'), ('eq', 'new', "'new'")]))
    assert_eq(run(lambda: delete(K("new"))), (('KeyError', 'K(new)'), [('hash', 'new'), ('hash', 'new')]))
    assert_eq(run(lambda: delete(K("x"))), (('ValueError', 'cannot remove local variables from FrameLocalsProxy'), [('hash', 'x'), ('eq', 'x', "'x'")]))
    assert_eq(run(lambda: p.pop(K("other"))), (14, [('hash', 'other'), ('hash', 'other'), ('eq', 'other', 'K(other)'), ('eq', 'other', "'other'")]))
    assert_eq(run(lambda: p.pop(K("other"))), (('KeyError', 'K(other)'), [('hash', 'other')]))
    assert_eq(run(lambda: p.pop(K("other"), 0)), (0, [('hash', 'other')]))
    assert_eq(run(lambda: p.setdefault(K("late"), 16)), (16, [('hash', 'late'), ('hash', 'late'), ('hash', 'late'), ('hash', 'late')]))
    assert_eq(run(lambda: p.setdefault(K("late", eq="raise"), 17)), (('KeyError', "'e'"), [('hash', 'late'), ('hash', 'late'), ('eq', 'late', 'K(late)'), ('eq', 'late', "'late'"), ('hash', 'late'), ('hash', 'late'), ('eq', 'late', 'K(late)'), ('eq', 'late', "'late'")]))
body()
q = current().f_locals
mod = 5
assert_eq(run(lambda: q[K("mod")]), (5, [('hash', 'mod'), ('eq', 'mod', "'mod'")]))
assert_eq(run(lambda: K("mod") in q), (True, [('hash', 'mod'), ('eq', 'mod', "'mod'")]))
assert_eq(run(lambda: q[S("mod")]), (5, [('S.eq', 'mod', "'mod'")]))

# A key with a Python __hash__ but no Python __eq__ compares by its own.
hashed_only = []
class HashedName(str):
    def __hash__(self):
        hashed_only.append(str(self))
        return str.__hash__(self)
class HashedOther:
    def __hash__(self): hashed_only.append("other"); return hash("x")
def hashed_body():
    x = 1
    try: raise ValueError
    except ValueError as e: p = e.__traceback__.tb_frame.f_locals
    return [p[HashedName("x")], HashedName("zz") in p, HashedOther() in p, hashed_only]
assert_eq(hashed_body(), [1, False, False, ["x", "zz", "other"]])

# pop() and deletion of an extra local find it by the key's Python
# __hash__ and __eq__ too; a deleted one is gone.
class ExtraHashed:
    def __hash__(self): return hash("q")
    def __eq__(self, other): return isinstance(other, ExtraHashed)
def extra_suspended():
    a = 1
    yield
extra_gen = extra_suspended(); next(extra_gen)
extra_proxy = extra_gen.gi_frame.f_locals
extra_proxy[ExtraHashed()] = 3
assert_eq([extra_proxy.pop(ExtraHashed()), extra_proxy.pop(ExtraHashed(), "d")], [3, "d"])
extra_proxy[ExtraHashed()] = 4
extra_proxy.__delitem__(ExtraHashed())
extra_proxy[ExtraHashed()] = 5
del extra_proxy[ExtraHashed()]
assert_raises(KeyError, extra_proxy.__delitem__, ExtraHashed())
assert_eq([ExtraHashed() in extra_proxy, len(extra_proxy)], [False, 1])
# A str subclass with a Python __hash__ and str's __eq__ finds a local by
# name; one whose hash collides with a local's name is not it.
str_log = []
class StrHashed(str):
    def __hash__(s):
        for _ in (): pass
        str_log.append(str(s)); return str.__hash__(s)
class StrCollides(str):
    def __hash__(s):
        for _ in (): pass
        str_log.append("c"); return hash("a")
def str_hashed():
    a, b = 1, 2
    try: raise KeyError
    except KeyError as e: p = e.__traceback__.tb_frame.f_locals
    out = [p[StrHashed("a")], StrHashed("b") in p, StrHashed("zz") in p, p.get(StrHashed("a")), p.get(StrHashed("q"), "d"),
           StrCollides("x") in p, p.get(StrCollides("y"), "none")]
    p[StrHashed("b")] = 5
    return out + [b], str_log
assert_eq(str_hashed(), ([1, True, False, 1, "d", False, "none", 5], ["a", "b", "zz", "a", "q", "c", "c", "b"]))
