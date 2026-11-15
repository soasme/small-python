# spec: PLS-315 26, 26.1.2
# description: d[k] = v, del d[k] and a target list's store on an
# instance of a dict subclass that keeps dict's __setitem__ and
# __delitem__ compare k with each stored key of its hash by the Python
# __eq__, which may loop, in insertion order: an equal key's entry takes
# the value or is removed, keeping its key, an absent key is appended or
# its deletion raises KeyError, and an exception of __eq__ propagates,
# leaving the dict as it was. Inside functions as at module level.
from harness import *

log = []
class Key:
    def __init__(self, n): self.n = n
    def __hash__(self): return 1
    def __eq__(self, other):
        for _ in range(2): pass
        log.append(("eq", self.n, other.n))
        if other.n == -1: raise ValueError("eq")
        return self.n == other.n
    def __repr__(self): return "K%d" % self.n
class Sub(dict): pass
def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)
def stores():
    d = Sub({Key(1): "one", Key(2): "two"})
    del log[:]
    d[Key(2)] = "TWO"
    d[Key(3)] = "three"
    def bad(): d[Key(-1)] = 0
    def gone(): del d[Key(5)]
    def bad_del(): del d[Key(-1)]
    out = [error(bad), error(gone), error(bad_del)]
    del d[Key(1)]
    a, d[Key(4)] = 0, "four"
    return out + [sorted((k.n, v) for k, v in d.items()), list(log)]

expected = [('ValueError', 'eq'),
 ('KeyError', 'K5'),
 ('ValueError', 'eq'),
 [(2, 'TWO'), (3, 'three'), (4, 'four')],
 [('eq', 1, 2),
  ('eq', 2, 2),
  ('eq', 1, 3),
  ('eq', 2, 3),
  ('eq', 1, -1),
  ('eq', 1, 5),
  ('eq', 2, 5),
  ('eq', 3, 5),
  ('eq', 1, -1),
  ('eq', 1, 1),
  ('eq', 2, 4),
  ('eq', 3, 4)]]

def main():
    return stores()

assert_eq(main(), expected)
assert_eq(stores(), expected)
