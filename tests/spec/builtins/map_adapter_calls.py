# spec: PLS-315 27.1.4, 27.1.6, 27.1.8, 27.1.1
# description: zip, enumerate and map take a map's items as it gives them,
# each calling its function, or its items' Python __str__, __hash__ and the
# other conversions, which may loop, after the items of the iterables
# before it, whether a loop, a consumer or a generator's yield from takes
# them; a map's StopIteration ends them, and an error drops the items
# taken for the zip's tuple.
from harness import *

log = []
def spin():
    # A loop puts a method's body on the machine.
    for _ in range(2): pass

class K:
    def __init__(self, v): self.v = v
    def __str__(self): spin(); log.append(self.v); return "k%d" % self.v
a, b = K(1), K(2)
def tagged(it):
    for x in it:
        log.append("i" + str(x))
        yield x

def check(expression, value, calls):
    log.clear()
    assert_eq(expression(), value)
    assert_eq(log, calls)

def main():
    check(lambda: list(zip(map(str, [a, b]), "xy")), [("k1", "x"), ("k2", "y")], [1, 2])
    check(lambda: list(enumerate(map(str, [b, a]), 5)), [(5, "k2"), (6, "k1")], [2, 1])
    check(lambda: dict(zip(map(str, [a]), map(str, [b]))), {"k1": "k2"}, [1, 2])
    check(lambda: list(map(len, map(str, [a, b]))), [2, 2], [1, 2])
    def loop():
        out = []
        for i, (s, t) in enumerate(zip(map(str, [a, b]), (7, 8, 9))):
            log.append("x")
            out.append((i, s, t))
        return out
    check(loop, [(0, "k1", 7), (1, "k2", 8)], [1, "x", 2, "x"])
    def gen():
        yield from zip("q", map(str, [b]))
    check(lambda: list(gen()), [("q", "k2")], [2])
    # The iterables before a map give their items first.
    check(lambda: list(zip(tagged([1, 2]), map(str, [a, b]))), [(1, "k1"), (2, "k2")], ["i1", 1, "i2", 2])
    def stop(x):
        spin()
        if x == 3: raise StopIteration
        return x
    check(lambda: (list(zip(map(stop, [1, 3, 4]), "abc")), list(enumerate(map(stop, [3])))), ([(1, "a")], []), [])
    # A map whose items call no Python, or a host's function, gives them too.
    check(lambda: (list(zip(map(str, [1, 2]), "ab")), list(zip(map("-".join, ["ab"]), "x"))),
          ([("1", "a"), ("2", "b")], [("a-b", "x")]), [])
main()

def fail(x):
    spin()
    if x == 2: raise ValueError("two")
    return x
z = zip("ab", map(fail, [1, 2, 3]))
assert_eq(next(z), ("a", 1))
assert_raises(ValueError, lambda: next(z), message="two")
assert_eq(list(z), [])
e = enumerate(map(fail, [2, 5]))
assert_raises(ValueError, lambda: list(e), message="two")
assert_eq(list(e), [(0, 5)])
