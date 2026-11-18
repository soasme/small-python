# spec: PLS-315 26.1.2, 7.3.2
# description: dict.__getitem__ called on a dict or on a dict subclass's
# instance, unbound or bound, hashes a key by its Python __hash__ once and
# compares each stored key of that hash with it by the stored key's Python
# __eq__, which may loop; a key absent so, or a native key absent among
# keys with a Python __eq__, calls the class's __missing__, also a
# staticmethod's or a classmethod's, which may loop, its result the call's
# value; so also called with its arguments unpacked, as set.remove and
# discard are. Exceptions of __hash__, __eq__ and __missing__ propagate; an
# __eq__ that empties the dict leaves the key absent. Inside functions as
# at module level.
from harness import *

log = []

class Key:
    def __init__(self, n, drop=None): self.n = n; self.drop = drop
    def __hash__(self):
        for _ in range(2): pass
        log.append(("hash", self.n))
        if self.n == "badhash": raise ValueError("hash")
        return 1
    def __eq__(self, other):
        for _ in range(2): pass
        log.append(("eq", self.n))
        if self.n == "bad": raise KeyError("eq")
        if self.drop is not None:
            self.drop.clear()
            self.drop = None
            return False
        return isinstance(other, Key) and other.n == self.n

class Counts(dict):
    def __missing__(self, key):
        for _ in range(2): pass
        log.append(("missing", getattr(key, "n", key)))
        if isinstance(key, int) and key == 9: raise LookupError("nine")
        return "default"

class Static(dict):
    @staticmethod
    def __missing__(key):
        for _ in range(2): pass
        return ("static", getattr(key, "n", key))

class Klass(dict):
    @classmethod
    def __missing__(cls, key):
        for _ in range(2): pass
        return (cls.__name__, getattr(key, "n", key))

def error(f, *args):
    try:
        f(*args)
    except Exception as e:
        return type(e).__name__, str(e)

def calls():
    plain = {Key(1): "one"}
    c = Counts({Key(1): "one", 7: "seven"})
    static, klass, bad = Static({Key(1): 1}), Klass({Key(1): 1}), Counts({Key("bad"): 0})
    moving = Counts()
    moving[Key(1, moving)] = "one"
    del log[:]
    out = [dict.__getitem__(plain, Key(1)), dict.__getitem__(c, Key(1)), c.__getitem__(Key(1)),
           dict.__getitem__(c, Key(2)), c.__getitem__(Key(3)), dict.__getitem__(c, 5), c.__getitem__(7)]
    out += [dict.__getitem__(static, Key(4)), Klass().__getitem__(Key(5)), dict.__getitem__(klass, 6)]
    out += [error(dict.__getitem__, plain, Key(2))[0], error(dict.__getitem__, bad, Key(2)), error(c.__getitem__, Key("badhash")),
            error(dict.__getitem__, c, 9), dict.__getitem__(moving, Key(8)), len(moving), list(log)]
    s = {Key(1)}
    del log[:]
    out += [error(lambda: set.remove(*(s, Key(2))))[0], error(lambda: s.discard(*(Key(3),))), dict.__getitem__(*(c, Key(1))),
            error(lambda: dict.__getitem__(*(plain, Key(4))))[0], list(log)]
    return out

expected = ["one", "one", "one", "default", "default", "default", "seven", ("static", 4), ("Klass", 5), ("Klass", 6),
            "KeyError", ("KeyError", "'eq'"), ("ValueError", "hash"), ("LookupError", "nine"), "default", 0,
            [("hash", 1), ("eq", 1), ("hash", 1), ("eq", 1), ("hash", 1), ("eq", 1), ("hash", 2), ("eq", 1), ("missing", 2),
             ("hash", 3), ("eq", 1), ("missing", 3), ("missing", 5), ("hash", 4), ("eq", 1), ("hash", 5),
             ("hash", 2), ("eq", 1), ("hash", 2), ("eq", "bad"), ("hash", "badhash"), ("missing", 9), ("hash", 8), ("eq", 1), ("missing", 8)],
            "KeyError", None, "one", "KeyError", [("hash", 2), ("eq", 1), ("hash", 3), ("eq", 1), ("hash", 1), ("eq", 1), ("hash", 4), ("eq", 1)]]

def main():
    return calls()

assert_eq(main(), expected)
assert_eq(calls(), expected)
