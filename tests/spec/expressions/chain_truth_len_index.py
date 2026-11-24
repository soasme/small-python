# spec: PLS-315 7.5.1, 7.2.4
# description: the truth of a comparison's result with no __bool__ is its
# __len__, converted by __index__ when it returns another object; a
# chain goes on with its right operand when the result is true and
# otherwise gives the result. In not, a conditional and a comprehension
# filter too.
from harness import *
log = []
class Idx:
    def __init__(s, n): s.n = n
    def __index__(s):
        for _ in (): pass
        log.append(("index", s.n)); return s.n
class Res:
    def __init__(s, n): s.n = n
    def __len__(s):
        for _ in (): pass
        log.append(("len", s.n)); return Idx(s.n)
class C:
    def __init__(s, n): s.n = n
    def __lt__(s, o): return Res(s.n)
def run():
    a, b, c = C(0), C(1), C(2)
    out = [a < b < c, b < c < a, (b < c < 5) is not None, not (a < b), 1 if a < b else 2, [x for x in (a, b) if x < c]]
    return [x.n if isinstance(x, (Res, C)) else [y.n for y in x] if isinstance(x, list) else x for x in out], log
pairs = [("len", 0), ("index", 0), ("len", 1), ("index", 1), ("len", 1), ("index", 1), ("len", 0), ("index", 0),
         ("len", 0), ("index", 0), ("len", 0), ("index", 0), ("len", 1), ("index", 1)]
assert_eq(run(), ([0, 2, True, True, 2, [1]], pairs))
