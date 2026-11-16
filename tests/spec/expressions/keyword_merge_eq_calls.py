# spec: PLS-315 13.3.4
# description: A call's ** of a dict merges its entries into the keywords
# gathered so far, each name keeping its stored hash: one equal in hash to
# a gathered name is compared by __eq__, the reflected __eq__ of a str
# subclass's name first, and an equal one raises TypeError naming the
# callee; NotImplemented leaves str's comparison, a false result keeps both
# names, an exception propagates, and an __eq__ that grows the merged dict
# raises RuntimeError. Inside functions as at module level.
from harness import *

log = []
source = {}

class Odd(str):
    __hash__ = str.__hash__
    def __eq__(self, other):
        for _ in range(2): pass
        log.append((str(self), str(other)))
        if str(self) == "r": raise LookupError("r")
        if str(self) == "n": return NotImplemented
        if str(self) == "m": source["grown"] = 0
        if str(self) in ("f", "m"): return False
        return str.__eq__(self, other)

def f(**kw): return sorted((type(k).__name__, str(k), v) for k, v in kw.items())

def merge(first, second):
    global source
    source = second
    del log[:]
    try:
        r = f(**first, **second)
    except Exception as e:
        r = type(e).__name__ + ": " + str(e)
    return r, log[:]

def results():
    return [merge({"a": 0}, {Odd("a"): 1}), merge({Odd("a"): 0}, {"a": 1}), merge({"n": 0}, {Odd("n"): 1}),
            merge({"f": 0}, {Odd("f"): 1}), merge({"r": 0}, {Odd("r"): 1}), merge({"m": 0}, {Odd("m"): 1}),
            merge({"a": 0}, {Odd("b"): 1, Odd("a"): 2}), merge({"a": 0, "b": 1}, {Odd("c"): 2})]

expected = [("TypeError: __main__.f() got multiple values for keyword argument 'a'", [('a', 'a')]), ("TypeError: __main__.f() got multiple values for keyword argument 'a'", [('a', 'a')]), ("TypeError: __main__.f() got multiple values for keyword argument 'n'", [('n', 'n')]), ([('Odd', 'f', 1), ('str', 'f', 0)], [('f', 'f'), ('f', 'f'), ('f', 'f')]), ('LookupError: r', [('r', 'r')]), ('RuntimeError: dict mutated during update', [('m', 'm'), ('m', 'm')]), ("TypeError: __main__.f() got multiple values for keyword argument 'a'", [('a', 'a')]), ([('Odd', 'c', 2), ('str', 'a', 0), ('str', 'b', 1)], [])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
