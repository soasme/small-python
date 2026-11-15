# spec: PLS-315 27.1.5, 7.7.2
# description: filter() over an iterator instance takes each item from its
# Python __next__ in turn, then tests it: by its truth for None or bool,
# its __bool__ called, by a builtin function, or by a Python function;
# the iterator's StopIteration ends the filter. In list(), a for loop, a
# comprehension and next(), inside functions as at module level.
from harness import *

log = []
class It:
    def __init__(self, items): self.items = list(items)
    def __iter__(self): return self
    def __next__(self):
        for _ in (): pass
        if not self.items: raise StopIteration
        x = self.items.pop(0); log.append(("next", x)); return x
class B:
    def __init__(self, v): self.v = v
    def __bool__(self): log.append(("bool", self.v)); return bool(self.v)
    def __repr__(self): return "B%d" % self.v
def keep(x): log.append(("keep", x)); return x % 2
def run():
    out = [list(filter(None, It([0, 1, 2, 0, 3]))), list(filter(keep, It([1, 2, 3]))), list(filter(bool, It([B(0), B(1)]))),
           list(filter(abs, It([0, -1]))), next(filter(None, It([0, 5]))), [x for x in filter(None, It([0, 7, 0]))]]
    f = filter(None, It([0, 4, 0, 6]))
    for x in f: out.append(x)
    try: next(filter(None, It([0])))
    except StopIteration: out.append("stop")
    return out

expected = "[[1, 2, 3], [1, 3], [B1], [-1], 5, [7], 4, 6, 'stop']"
expected_log = "[('next', 0), ('next', 1), ('next', 2), ('next', 0), ('next', 3), ('next', 1), ('keep', 1), ('next', 2), ('keep', 2), ('next', 3), ('keep', 3), ('next', B0), ('bool', 0), ('next', B1), ('bool', 1), ('next', 0), ('next', -1), ('next', 0), ('next', 5), ('next', 0), ('next', 7), ('next', 0), ('next', 0), ('next', 4), ('next', 0), ('next', 6), ('next', 0)]"
assert_eq(repr(run()), expected)
assert_eq(repr(log), expected_log)
log.clear()
assert_eq((list(filter(None, It([0, 8]))), log), ([8], [("next", 0), ("next", 8)]))
