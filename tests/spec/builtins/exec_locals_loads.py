# spec: PLS-315 9.3.1, 19.3.14, 19.3.15
# description: code that exec() and eval() run loads its names from a
# locals mapping through the mapping's Python __getitem__, which may loop,
# once per load in evaluation order, an augmented assignment's name too;
# a KeyError falls back to the globals and then the builtins, a missing
# name is a NameError, and another exception propagates. A dict subclass
# and a mapping of no dict base, inside functions as at module level.
from harness import *

log = []

class Locals(dict):
    def __getitem__(self, k):
        for _ in (): pass
        log.append(k)
        if k == "boom": raise LookupError(k)
        return dict.__getitem__(self, k)

class Mapping:
    def __init__(self, **items): self.items = items
    def __getitem__(self, k):
        for _ in (): pass
        log.append(k)
        return self.items[k]
    def __setitem__(self, k, v): self.items[k] = v
    def keys(self): return self.items.keys()

def runs():
    l = Locals(a=1)
    exec("b = a + a\nb += a\nfor i in (a, b): c = i\nd = len if a else str\ne = g", {"g": 5}, l)
    m = Mapping(x=2)
    exec("y = x * x\nz = [x, abs]", {}, m)
    return [dict(l), m.items, eval("a + b", {}, l), eval("x - 1", {}, m), eval("abs(g)", {"g": -3}, Locals())]

expected = [{"a": 1, "b": 3, "i": 3, "c": 3, "d": len, "e": 5}, {"x": 2, "y": 4, "z": [2, abs]}, 4, 1, 3]
expected_log = ["a", "a", "b", "a", "a", "b", "i", "i", "a", "len", "g", "x", "x", "x", "abs", "a", "b", "x", "abs", "g"]
assert_eq(runs(), expected)
assert_eq(log, expected_log)
log.clear()

l = Locals(a=4)
exec("b = a", {}, l)
assert_eq((l["b"], log), (4, ["a", "b"]))
log.clear()

def errors():
    out = []
    for source in ("missing", "boom + 1"):
        try: exec(source, {}, Locals())
        except NameError as e: out.append(str(e))
        except LookupError as e: out.append(e.args)
    return out

assert_eq(errors(), ["name 'missing' is not defined", ("boom",)])
assert_eq(log, ["missing", "boom"])
