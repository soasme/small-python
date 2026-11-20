# spec: PLS-315 25.3.2, 25.5.2, 25.1.3
# description: a range's index() and count() of an instance, and `in`,
# compare it with each item in turn, the instance's Python __eq__ called
# with the item until a match, and the truth of what it returns taken by
# its __bool__ or __len__; a missing item raises the sequence's ValueError,
# an __eq__'s exception propagates. list.index, list.count, list.remove,
# tuple.index, tuple.count, range.index and range.count called through the
# class search the same way, a subclass instance by its sequence. Inside
# functions as at module level.
from harness import *

log = []
class Eq:
    def __init__(self, v): self.v = v
    def __eq__(self, other):
        log.append(other)
        return other == self.v
class Truth:
    def __init__(self, v): self.v = v
    def __bool__(self):
        log.append("bool")
        return self.v
class Sized:
    def __len__(self):
        log.append("len")
        return 0
class Answers:
    def __init__(self, answer): self.answer = answer
    def __eq__(self, other): return self.answer(other)
class Raises:
    def __eq__(self, other): raise LookupError(other)
class Plain:
    pass
class Seq(list):
    def index(self, *args): return "overridden"

def taken(f):
    try:
        r = f()
    except Exception as e:
        r = (type(e).__name__, str(e))
    got = list(log); log.clear()
    return r, got

r = range(5)
assert_eq(taken(lambda: r.index(Eq(3))), (3, [0, 1, 2, 3]))
assert_eq(taken(lambda: r.count(Eq(2))), (1, [0, 1, 2, 3, 4]))
assert_eq(taken(lambda: Eq(1) in r), (True, [0, 1]))
assert_eq(taken(lambda: Eq(9) not in r), (True, [0, 1, 2, 3, 4]))
assert_eq(taken(lambda: r.index(Eq(9))), (("ValueError", "sequence.index(x): x not in sequence"), [0, 1, 2, 3, 4]))
assert_eq(taken(lambda: range(10, 0, -3).index(Eq(4))), (2, [10, 7, 4]))
assert_eq(taken(lambda: range(2 ** 70, 2 ** 70 + 3).index(Eq(2 ** 70 + 1))), (1, [2 ** 70, 2 ** 70 + 1]))
assert_eq(taken(lambda: r.index(Answers(lambda o: Truth(o == 2)))), (2, ["bool"] * 3))
assert_eq(taken(lambda: r.count(Answers(lambda o: Sized()))), (0, ["len"] * 5))
assert_eq(taken(lambda: r.index(Answers(lambda o: Truth(1)))), (("TypeError", "Truth.__bool__() must return a bool, not int"), ["bool"]))
assert_eq(taken(lambda: r.count(Answers(lambda o: NotImplemented))), (0, []))
assert_eq(taken(lambda: r.index(Raises())), (("LookupError", "0"), []))
assert_eq(taken(lambda: (r.count(Plain()), Plain() in r)), ((0, False), []))
assert_eq(taken(lambda: range(10 ** 5).count(Plain())), (0, []))

l = [1, 2, 3, 2]
assert_eq(taken(lambda: list.index(l, Eq(2))), (1, [1, 2]))
assert_eq(taken(lambda: list.index(l, Eq(2), 2)), (3, [3, 2]))
assert_eq(taken(lambda: list.index(l, Eq(2), 2, 3)), (("ValueError", "list.index(x): x not in list"), [3]))
assert_eq(taken(lambda: list.count(l, Eq(2))), (2, [1, 2, 3, 2]))
assert_eq(taken(lambda: tuple.count((2, 2), Eq(2))), (2, [2, 2]))
assert_eq(taken(lambda: tuple.index((1, 2), Eq(5))), (("ValueError", "tuple.index(x): x not in tuple"), [1, 2]))
assert_eq(taken(lambda: range.index(r, Eq(3))), (3, [0, 1, 2, 3]))
assert_eq(taken(lambda: range.count(r, Eq(3))), (1, [0, 1, 2, 3, 4]))
removed = list(l)
assert_eq(taken(lambda: (list.remove(removed, Eq(3)), removed)), ((None, [1, 2, 2]), [1, 2, 3]))
assert_eq(taken(lambda: (list.index(Seq([1, 2]), Eq(2)), Seq([1, 2]).index(Eq(2)))), ((1, "overridden"), [1, 2]))
assert_eq(taken(lambda: list.index((1, 2), Eq(2)))[0][0], "TypeError")
assert_eq(taken(lambda: tuple.index(range(3), Eq(1)))[0][0], "TypeError")
index = list.index
assert_eq(taken(lambda: index(l, Eq(3))), (2, [1, 2, 3]))
def inside():
    return r.index(Eq(1)), r.count(Eq(1)), Eq(4) in r, list.index(l, Eq(3)), tuple.count((3, 3), Eq(3))
assert_eq(taken(inside), ((1, 1, True, 2, 2), [0, 1, 0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 1, 2, 3, 3, 3]))
