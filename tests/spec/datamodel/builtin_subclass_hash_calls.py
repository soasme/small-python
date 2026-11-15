# spec: PLS-315 7.5.7
# description: a dict or set display, item, membership test or store with
# a key that is an instance of a subclass of str, tuple, int or frozenset
# defining __hash__ calls that Python __hash__, which may loop, once per
# hash; its exception propagates from the display. A subclass without its
# own __hash__ hashes as its builtin value. Inside functions as at module
# level.
from harness import *

log = []

class K(str):
    def __hash__(self):
        for _ in (): pass
        log.append(("str", str(self)))
        return str.__hash__(self)

class T(tuple):
    def __hash__(self):
        for _ in (): pass
        log.append(("tuple", self[0]))
        return 5

class I(int):
    def __hash__(self):
        for _ in (): pass
        log.append(("int", int(self)))
        raise KeyError("int")

class F(frozenset):
    def __hash__(self):
        for _ in (): pass
        log.append("frozenset")
        return 1

class Plain(str): pass

def lookups():
    d = {K("a"): 1, T((2,)): 2, F({3}): 3}
    s = {K("b")}
    out = [d[K("a")], T((2,)) in d, K("b") in s, "a" in d, d[F({3})], {Plain("p"): 4}["p"]]
    d[K("c")] = 5
    out.append(len(d))
    try: {I(6): 1}
    except KeyError as e: out.append(e.args)
    return out

expected = [1, True, True, True, 3, 4, 4, ("int",)]
expected_log = [("str", "a"), ("tuple", 2), "frozenset", ("str", "b"), ("str", "a"), ("tuple", 2), ("str", "b"),
                "frozenset", ("str", "c"), ("int", 6)]
assert_eq(lookups(), expected)
assert_eq(log, expected_log)
log.clear()
d = {K("x"): 1}
assert_eq((d[K("x")], log), (1, [("str", "x"), ("str", "x")]))
