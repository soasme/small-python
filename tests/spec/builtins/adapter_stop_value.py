# spec: PLS-315 27.1.1, 27.1.8, 13.16.3
# description: enumerate, filter, map and zip stop by raising the
# StopIteration their iterator raised, so a generator's return value
# reaches next() through nested adapters and is the value of a yield
# from over them; a strict zip or map raises one without a value, and
# next() with a default gives the default.
from harness import assert_eq

def g(n=1, r=9):
    for i in range(n): yield i
    return r

def d(a):
    r = yield from a
    return ("r", r)

def drive(it):
    out = []
    try:
        while True: out.append(next(it))
    except StopIteration as e:
        return out, e.value

class Even:
    def __init__(self, v): self.v = v
    def __bool__(self):
        for _ in (): pass
        return self.v % 2 == 0

def run():
    return [drive(zip(g())), drive(enumerate(g())), drive(map(abs, g())), drive(filter(None, g())),
            drive(zip(enumerate(g()))), drive(d(zip(g()))), drive(d(enumerate(g()))), drive(d(map(lambda x: x, g()))),
            drive(d(map(abs, filter(lambda x: Even(x), g(5))))), drive(d(zip(g(2, 7), g(3, 8)))),
            drive(d(zip(g(2), g(2), strict=True))), drive(d(map(lambda a, b: a + b, g(2), g(2), strict=True))),
            [next(zip(enumerate(g(0))), "default"), next(map(abs, filter(None, g(0))), "default")],
            [x for x in zip(enumerate(g(3)))]]

assert_eq(run(), [([(0,)], 9), ([(0, 0)], 9), ([0], 9), ([], 9),
                  ([((0, 0),)], 9), ([(0,)], ("r", 9)), ([(0, 0)], ("r", 9)), ([0], ("r", 9)),
                  ([0, 2, 4], ("r", 9)), ([(0, 0), (1, 1)], ("r", 7)),
                  ([(0, 0), (1, 1)], ("r", None)), ([0, 2], ("r", None)),
                  ["default", "default"], [((0, 0),), ((1, 1),), ((2, 2),)]])
