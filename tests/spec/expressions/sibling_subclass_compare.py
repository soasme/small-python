# spec: PLS-315 7.2.4, 13.10.1, 25.5.2
# description: a number, exact or of a subclass that defines no comparison
# of its own, compared with an instance of a number's subclass that is not
# a subclass of its class, answers by its own number method before the
# other's reflected Python method, which is never called; operators, in,
# count(), index(), dict values, min(), max() and sequence comparison all
# keep that order, and the reflected method is still called when the
# other's class is a subclass of the first's.
from harness import *

log = []
class I(int):
    def __eq__(self, other):
        for _ in (): pass
        log.append("I.eq")
        return int(self) % 10 == other % 10
    def __lt__(self, other):
        for _ in (): pass
        log.append("I.lt")
        return int(self) % 10 < other % 10
    def __gt__(self, other):
        for _ in (): pass
        log.append("I.gt")
        return int(self) % 10 > other % 10
    __hash__ = int.__hash__
class J(int): pass
class B(J): pass
class K(int):
    def __eq__(self, other):
        log.append("K.eq")
        return NotImplemented
    __hash__ = int.__hash__
def run(f):
    del log[:]
    r = f()
    return r, list(log)

def compare(x, y):
    return x == y, x != y, x < y, x > y
# Each item is compared with the searched value, the item on the left.
def search(x, y):
    return x in [y], [y].count(x), (y,).index(x) if x in (y,) else -1, x in {0: y}.values()
def order(x, y):
    return [x] == [y], (x, 1) < (y, 2), min(y, x), max(y, x)

for x in (J(3), B(3), 13.0, True):
    # x answers itself: 13 and 3 differ, and I's methods are not called.
    assert_eq(run(lambda: compare(x, I(13)))[1], [])
    assert_eq(run(lambda: compare(x, I(1)))[0][:2], (x == 1, x != 1))
    assert_eq(run(lambda: search(I(13), x))[1], [])
    assert_eq(run(lambda: order(x, I(13)))[1], [])
assert_eq(run(lambda: compare(J(3), I(13))), ((False, True, True, False), []))
assert_eq(run(lambda: search(I(13), J(3))), ((False, 0, -1, False), []))
assert_eq(run(lambda: order(J(3), I(13))), ((False, True, 3, 13), []))
assert_eq(run(lambda: J(3) == I(13) == I(23)), (False, []))

# I first when it is the left operand, or a subclass of the left's class.
# I has no __ne__ of its own: != is int's.
assert_eq(run(lambda: compare(I(13), J(3))), ((True, True, False, False), ["I.eq", "I.lt", "I.gt"]))
assert_eq(run(lambda: compare(3, I(13))), ((True, True, False, False), ["I.eq", "I.gt", "I.lt"]))
assert_eq(run(lambda: search(I(13), 3)), ((True, 1, 0, True), ["I.eq"] * 5))
assert_eq(run(lambda: search(J(3), I(13))), ((True, 1, 0, True), ["I.eq"] * 5))

# A class that defines its method calls it first; its NotImplemented
# leaves I's reflected one.
assert_eq(run(lambda: K(3) == I(13)), (True, ["K.eq", "I.eq"]))
assert_eq(run(lambda: I(13) in [K(3)]), (True, ["K.eq", "I.eq"]))
assert_eq(run(lambda: [I(13)].count(K(3))), (1, ["I.eq"]))
assert_eq(run(lambda: [K(3)].count(I(13))), (1, ["K.eq", "I.eq"]))
