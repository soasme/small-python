# spec: PLS-315 25.1.4, 19.3.34
# description: A sort's comparison of two keys whose Python __lt__ returns
# NotImplemented calls the other key's reflected __gt__ with the pair
# swapped, and a tuple item's __eq__ that returns NotImplemented falls
# back to the other item's __eq__ and then to identity, as RichCompare
# does; the reflected result orders the keys, its exception propagates
# out of the sort, and two NotImplemented answers raise TypeError. With
# and without a key, reversed, by list.sort, inside functions as at
# module level.
from harness import *

log = []

class K:
    def __init__(self, v): self.v = v
    def __lt__(self, other):
        log.append(("lt", self.v, other.v))
        return NotImplemented
    def __gt__(self, other):
        for _ in (): pass
        log.append(("gt", self.v, other.v))
        if self.v == 9: raise KeyError(9)
        return self.v > other.v
    def __eq__(self, other):
        log.append(("eq", self.v, other.v))
        return NotImplemented

class Never:
    def __lt__(self, other): return NotImplemented
    def __gt__(self, other): return NotImplemented

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def reflected():
    # Each reflected call swaps the pair of a declined __lt__ call.
    declined = {(a, b) for op, a, b in log if op == "lt"}
    return all((b, a) in declined for op, a, b in log if op == "gt") and any(op == "gt" for op, a, b in log)

def results():
    del log[:]
    out = [[k.v for k in sorted([K(3), K(1), K(2)])], reflected()]
    del log[:]
    out += [[k.v for k in sorted([K(3), K(1), K(4), K(2)], reverse=True)], reflected()]
    del log[:]
    ks = [K(2), K(0), K(1)]
    ks.sort(key=lambda k: k)
    out += [[k.v for k in ks], reflected()]
    del log[:]
    out += [[t[1] for t in sorted([(K(1), 0), (K(0), 1)])], ("eq", 0, 1) in log or ("eq", 1, 0) in log, reflected()]
    out += [error(lambda: sorted([K(9), K(1)])), error(lambda: sorted([Never(), Never()]))]
    return out

expected = [[1, 2, 3], True, [4, 3, 2, 1], True, [0, 1, 2], True, [1, 0], True, True,
            ("KeyError", "9"), ("TypeError", "'<' not supported between instances of 'Never' and 'Never'")]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
