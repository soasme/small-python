# spec: PLS-315 25.4.1
# description: Slices compare as the tuples of their parts: a part's
# Python __eq__ and __lt__, which may loop, run once each as a tuple's
# do, an error propagating, at each part and in a comparison chain; a
# slice compared with itself calls neither.
from harness import *

log = []
class E:
    def __init__(s, v): s.v = v
    def __eq__(s, o):
        for _ in (): pass
        log.append(("eq", s.v, getattr(o, "v", o)))
        if s.v == "raise": raise KeyError(s.v)
        return s.v == getattr(o, "v", o)
    def __lt__(s, o):
        for _ in (): pass
        log.append(("lt", s.v, getattr(o, "v", o)))
        return s.v < getattr(o, "v", o)
    __hash__ = None
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
a1, a2, b = E(1), E(1), E(2)
s = slice(a1)
cases = [lambda: slice(a1) == slice(a2), lambda: slice(a1) != slice(b), lambda: s == s, lambda: s < s, lambda: s <= s,
         lambda: slice(1, a1) == slice(1, a2), lambda: slice(1, 2, a1) == slice(1, 2, b), lambda: slice(E("raise")) == slice(a1),
         lambda: slice(a1) < slice(b), lambda: slice(b) < slice(a1), lambda: slice(1, a1) <= slice(1, b), lambda: slice(1, 2) < slice(1, 3),
         lambda: slice(a1) == (a1, None, None), lambda: slice(1, 2) == slice(1, 2), lambda: slice(a1) < slice(a1, 1) < slice(a1, 2),
         lambda: [slice(a1) == slice(a2) for _ in range(2)]]
assert_eq([run(f) for f in cases],
          [(True, [("eq", 1, 1)]), (True, [("eq", 1, 2)]), (True, []), (False, []), (True, []), (True, [("eq", 1, 1)]),
           (False, [("eq", 1, 2)]), (("KeyError", "'raise'"), [("eq", "raise", 1)]), (True, [("eq", 1, 2), ("lt", 1, 2)]),
           (False, [("eq", 2, 1), ("lt", 2, 1)]),
           (("TypeError", "'<=' not supported between instances of 'E' and 'E'"), [("eq", 1, 2)]), (True, []), (False, []),
           (True, []), (("TypeError", "'<' not supported between instances of 'NoneType' and 'E'"), [("eq", 1, None)]),
           ([True, True], [("eq", 1, 1), ("eq", 1, 1)])])
