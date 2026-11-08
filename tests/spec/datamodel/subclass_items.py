# spec: PLS-315 7.3.2, 27.4.1
# description: x[k] of an instance of a dict subclass finds a present key
# without other calls and calls the class's __missing__ with an absent one,
# its result the subscription's value and its exception raised there; a
# stored key with k's hash is compared once. A Python __getitem__ of a
# dict or list subclass is called instead, and dict's own reaches
# __missing__ too; a wrong arity is the method's TypeError. Each may loop,
# inside functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Counts(dict):
    def __missing__(self, key):
        spin()
        log.append(("missing", key))
        if key == "bad":
            raise LookupError("no " + key)
        self[key] = 0
        return 0

class Key:
    def __hash__(self): return hash(5)
    def __eq__(self, other):
        log.append(("eq", other))
        return other == 5

class Logged(dict):
    def __getitem__(self, key):
        spin()
        log.append(("getitem", key))
        return super().__getitem__(key) * 10
    def __missing__(self, key):
        spin()
        log.append(("logged missing", key))
        return -1

class Narrow(dict):
    def __missing__(self): spin()

class Items(list):
    def __getitem__(self, i):
        spin()
        log.append(("item", i))
        return list.__getitem__(self, i) + 1

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def items():
    del log[:]
    d = Counts(a=1)
    d[2] = 3
    out = [d["a"], d[2], d["b"], d[None], d[2.0], d[True], d[(1, 2)], d["b"], sorted(map(str, d))]
    k = Counts()
    k[Key()] = "key"
    out += [k[5], error(lambda: d["bad"]), error(lambda: Narrow()[1])]
    g = Logged(x=1)
    out += [g["x"], g["y"], Items([1, 2])[1], Items([3])[-1]]
    out.append(list(log))
    return out

expected = [1, 3, 0, 0, 3, 0, 0, 0, ['(1, 2)', '2', 'None', 'True', 'a', 'b'],
            "key", ("LookupError", "no bad"),
            ("TypeError", "Narrow.__missing__() takes 1 positional argument but 2 were given"), 10, -10, 3, 4,
            [("missing", "b"), ("missing", None), ("missing", True), ("missing", (1, 2)),
             ("eq", 5), ("missing", "bad"),
             ("getitem", "x"), ("getitem", "y"), ("logged missing", "y"), ("item", 1), ("item", -1)]]

def main():
    return items()

assert_eq(main(), expected)
assert_eq(items(), expected)
