# spec: PLS-315 7.8.3, 13.10
# description: x in a list or tuple, x bytes, a bytearray, a complex, a
# range, a set, a slice, a builtin function or another builtin value,
# compares each item v with x as v == x in order: an instance item's
# __eq__, which may loop, sees x itself, the first true result stops the
# search, and items before it compare natively. Inside functions as at
# module level, and in an if or while test.
from harness import *

log = []

class Key:
    def __init__(self, want): self.want = want
    def __eq__(self, other):
        for _ in range(2): pass
        log.append(type(other).__name__)
        return other == self.want
    __hash__ = None

def searches():
    del log[:]
    out = [b"x" in [1, b"y", Key(b"x"), Key(b"x")], bytearray(b"z") in (Key(b"q"), Key(b"z")),
           3j not in [Key(1), 3j], range(2) in [range(1), Key(range(2))], b"q" in [Key(b"r")], list(log)]
    del log[:]
    tests = []
    if b"a" in [Key(b"a")]: tests.append("in")
    if range(3) not in (Key(range(4)),): tests.append("not in")
    n = 0
    while complex(n) not in [Key(2j), Key(3)]: n += 1
    out += [tests, n, list(log)]
    del log[:]
    return out + [{1} in [1, "a", Key({1})], frozenset() not in (Key(frozenset()),), slice(1) in [Key(0)],
                  len in [Key(len)], list(log)]

expected = [True, True, False, True, False, ["bytes", "bytearray", "bytearray", "complex", "range", "bytes"],
            ["in", "not in"], 3, ["bytes", "range"] + ["complex"] * 8,
            True, False, False, True, ["set", "frozenset", "slice", "builtin_function_or_method"]]
assert_eq(searches(), expected)

def nested():
    return searches()

assert_eq(nested(), expected)
