# spec: PLS-315 10.2.1, 26.3.1
# description: Calling a list or set subclass whose Python __new__ returns
# an instance of the class, and which keeps the builtin __init__, then runs
# list.__init__ or set.__init__ on that instance with the call's argument:
# the instance is emptied and takes a generator's items, which may loop,
# or a list's items hashed by their Python __hash__, in order, and is the
# call's value; an exception from the source propagates, the items before
# it kept, and an instance of another class is not initialized. Inside
# functions as at module level.
from harness import *

log = []

def items(n, bad=False):
    for i in range(n):
        for _ in range(2): pass
        log.append(i)
        yield i
    if bad: raise LookupError("source")

class Key:
    def __init__(self, n): self.n = n
    def __hash__(self):
        log.append(("hash", self.n))
        return self.n
    def __eq__(self, other): return self.n == other.n

kept = []

class Seq(list):
    def __new__(cls, *args):
        for _ in range(2): pass
        log.append("new")
        return kept[0] if kept else super().__new__(cls)

class Bag(set):
    def __new__(cls, *args):
        log.append("new")
        return super().__new__(cls)

class Other(list):
    def __new__(cls, *args): return [9]

def calls():
    del log[:], kept[:]
    out = [Seq(items(3)), type(Seq(items(1))) is Seq, sorted(Bag(items(2))), sorted(k.n for k in Bag([Key(4), Key(5)]))]
    old = Seq([7, 8])
    kept.append(old)
    out += [Seq(items(2)) is old, old]
    del kept[:]
    try:
        Seq(items(2, True))
    except LookupError as e:
        out.append(str(e))
    kept.append(old)
    try:
        Seq(items(1, True))
    except LookupError as e:
        out += [str(e), old]
    del kept[:]
    out += [Other(items(2)), list(log)]
    return out

expected = [[0, 1, 2], True, [0, 1], [4, 5], True, [0], 'source', 'source', [0], [9],
            ['new', 0, 1, 2, 'new', 0, 'new', 0, 1, 'new', ('hash', 4), ('hash', 5), 'new', 'new', 0, 1, 'new', 0, 1,
             'new', 0]]

def main():
    return calls()

assert_eq(main(), expected)
assert_eq(calls(), expected)
