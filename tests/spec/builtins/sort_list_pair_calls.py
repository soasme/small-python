# spec: PLS-315 25.1.4, 7.2.4
# description: sorting lists of lists compares two lists as list ordering
# does: their items by __eq__ until a pair is unequal, which then decides
# by __lt__, else the shorter is less; each Python method may loop; a
# NotImplemented from __eq__ asks the other item's reflected one, then
# identity; a result's Python __bool__ gives its truth; an exception
# propagates; a list and a tuple are unordered. A method that empties or
# shortens the list it compares, which the sort reads again, leaves the
# result a permutation of the lists. The order of comparisons is the
# implementation's (Annex D), so only the methods called are checked.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class V:
    def __init__(self, n, home=None, how=None): self.n = n; self.home = home; self.how = how
    def __eq__(self, o):
        spin(); log.append("eq")
        if self.how == "clear" and self.home is not None: self.home.clear()
        if self.how == "pop" and self.home: self.home.pop()
        if self.how == "raise": raise KeyError("eq")
        if self.how == "ni": return NotImplemented
        return isinstance(o, V) and self.n == o.n
    def __lt__(self, o):
        spin(); log.append("lt")
        if self.how == "truth": return T(self.n < o.n)
        return self.n < o.n
    def __repr__(self): return "V%d" % self.n
    __hash__ = None

class T:
    def __init__(self, v): self.v = v
    def __bool__(self): spin(); log.append("bool"); return self.v

def homed(n, how, *rest):
    l = []
    l.append(V(n, l, how)); l.extend(rest)
    return l

def run(f):
    del log[:]
    try:
        r = repr(f())
    except Exception as e:
        r = (type(e).__name__, str(e))
    return r, sorted(set(log))

def permutation(lists):
    out = sorted(lists)
    return len(out) == len(lists) and all(any(x is y for y in lists) for x in out)

def results():
    return [run(lambda: sorted([[V(2)], [V(1)], [V(1), 0]])),
            run(lambda: sorted([[V(1), V(3)], [V(1), V(2)]], reverse=True)),
            run(lambda: sorted([[V(1, how="raise")], [V(1, how="raise")]])),
            run(lambda: sorted([[V(1, how="ni")], [V(1, how="ni")]])),
            run(lambda: sorted([[V(2, how="truth")], [V(1, how="truth")]])),
            run(lambda: sorted([[1, V(2)], [1, V(1)], [0]])),
            run(lambda: sorted([[V(1)], (V(0),)])),
            run(lambda: (lambda l: (l.sort(), l)[1])([[V(3)], [V(1)], [V(2)]])),
            run(lambda: permutation([homed(1, "clear", 5), homed(1, "clear", 4), homed(1, "clear", 3)])),
            run(lambda: permutation([homed(1, "pop", V(9)), homed(1, None, V(8)), homed(1, "pop", V(7))]))]

expected = [("[[V1], [V1, 0], [V2]]", ["eq", "lt"]), ("[[V1, V3], [V1, V2]]", ["eq", "lt"]),
            (("KeyError", "'eq'"), ["eq"]), ("[[V1], [V1]]", ["eq", "lt"]),
            ("[[V1], [V2]]", ["bool", "eq", "lt"]), ("[[0], [1, V1], [1, V2]]", ["eq", "lt"]),
            (("TypeError", "'<' not supported between instances of 'tuple' and 'list'"), []),
            ("[[V1], [V2], [V3]]", ["eq", "lt"]), ("True", ["eq"]), ("True", ["eq", "lt"])]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
