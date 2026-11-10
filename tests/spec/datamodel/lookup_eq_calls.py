# spec: PLS-315 26, 7.5.7
# description: A dict subscript, store and deletion, in of a dict,
# frozendict, set or frozenset, dict and set displays and set
# comprehensions compare an instance key with each stored key of the same
# hash by ==, the stored key's __eq__ first unless the key's class is a
# subclass of its class, which may loop; a key itself matches without a call, NotImplemented
# leaves the reflected method and then identity, a false result goes on
# to the next key of that hash, a store of an equal key keeps the stored
# key with the new value, a comparison that empties the dict ends it
# unfound, a key of no Python __eq__ compares by identity, and an
# __eq__'s exception propagates, with a __hash__ in Python or not, inside
# functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Key:
    def __init__(self, tag, answer=True): self.tag = tag; self.answer = answer
    def __hash__(self): return 1
    def __eq__(self, other):
        spin()
        log.append(("eq", self.tag, getattr(other, "tag", other)))
        if self.answer == "bad": raise KeyError("eq")
        if self.answer == "clear":
            table.clear()
        return self.answer

class Sub(Key):
    __hash__ = Key.__hash__
    def __eq__(self, other):
        spin()
        log.append(("sub", self.tag))
        return True

class Hasher:
    def hash(self): return 1

class Native:
    __hash__ = Hasher().hash
    def __init__(self, tag): self.tag = tag
    def __eq__(self, other):
        spin()
        log.append(("native", self.tag))
        return isinstance(other, Native)

class BadHash:
    def __hash__(self): raise KeyError("hash")

class Plain:
    def __hash__(self): return 1

class Arity:
    def __hash__(self): return 1
    def __eq__(self): spin()

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, getattr(e.args[0], "tag", str(e))

table = {}

def results():
    global table
    del log[:]
    a, b = Key("a"), Key("b")
    d = {a: "A"}
    no, maybe = Key("no", False), Key("maybe", NotImplemented)
    two = {no: "N", Key("yes"): "Y"}
    table = {Key("clear", "clear"): "C"}
    n = Native("n")
    out = [d[b], d[a], b in d, b not in d, Key("s") in {a}, Key("f") in frozenset([a]), frozendict({a: "F"})[b],
           two[Key("x")], error(lambda: {no: 1}[Key("y")]), {maybe: 1}.get(maybe), error(lambda: {maybe: 1}[Key("z")]),
           d[Sub("c")], error(lambda: table[Key("t")]), {n: "native"}[Native("m")], Native("k") in {n},
           error(lambda: {Key("bad", "bad"): 1}[Key("w")]), error(lambda: {Arity(): 1}[Key("v")])]
    stored = {no: "N"}
    stored[Key("u")] = "U"
    stored[Key("v", False)] = "V"
    del stored[Key("w")]
    natives = {Native("p"): 1}
    natives[Native("q")] = 2
    del natives[Native("r")]
    natives[Native("s")] = 3
    out += [sorted(v for v in stored.values()), len(natives), len({no, Key("set")}), len({k for k in (no, Key("comp"))}), len({Key("d"): 1, Key("e"): 2}),
            error(lambda: delete({no: 1}, Key("x", False))), error(lambda: {}[BadHash()]), error(lambda: BadHash() in {}),
            Plain() in {1: "one"}, error(lambda: {1: "one"}[Plain()])[0]]
    out.append(list(log))
    return out

def delete(d, k):
    del d[k]

expected = ['A', 'A', True, False, True, True, 'F', 'Y', ('KeyError', 'y'), 1, 1, 'A', ('KeyError', 't'), 'native', True,
            ('KeyError', "'eq'"), ('TypeError', 'Arity.__eq__() takes 1 positional argument but 2 were given'),
            ['N'], 1, 2, 2, 1, ('KeyError', 'x'), ('KeyError', "'hash'"), ('KeyError', "'hash'"), False, 'KeyError',
            [('eq', 'no', 'yes'), ('eq', 'a', 'b'), ('eq', 'a', 'b'), ('eq', 'a', 'b'), ('eq', 'a', 's'),
             ('eq', 'a', 'f'), ('eq', 'a', 'b'), ('eq', 'no', 'x'), ('eq', 'yes', 'x'), ('eq', 'no', 'y'),
             ('eq', 'maybe', 'z'), ('eq', 'z', 'maybe'), ('sub', 'c'), ('eq', 'clear', 't'), ('native', 'n'),
             ('native', 'n'), ('eq', 'bad', 'w'), ('eq', 'no', 'u'), ('eq', 'no', 'v'), ('eq', 'u', 'v'), ('eq', 'no', 'w'),
             ('eq', 'u', 'w'), ('native', 'p'), ('native', 'p'), ('eq', 'no', 'set'), ('eq', 'no', 'comp'), ('eq', 'd', 'e'), ('eq', 'no', 'x')]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
