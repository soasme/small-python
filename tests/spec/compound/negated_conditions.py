# spec: PLS-315 13.11, 13.12, 13.14, 15.1, 15.2, 16.1
# description: A condition negated by not, once or more, takes its operand's
# truth: __bool__ or __len__ runs once, its errors propagate, and the branch
# goes the other way, in if, elif, while, conditional expressions,
# comprehension conditions and match guards, with True, False and None.
from harness import *

calls = []


class Truth:
    def __init__(self, value):
        self.value = value

    def __bool__(self):
        calls.append("bool")
        return self.value


class Sized:
    def __init__(self, size):
        self.size = size

    def __len__(self):
        calls.append("len")
        return self.size


class Broken:
    def __bool__(self):
        raise ValueError("no truth")


class Odd:
    def __bool__(self):
        return 1


def branch(x):
    if not x:
        return "falsy"
    elif not not x:
        return "truthy"
    return "never"


assert_same(branch(0), "falsy")
assert_same(branch(1), "truthy")
assert_same(branch(None), "falsy")
assert_same(branch(True), "truthy")
assert_same(branch(False), "falsy")
assert_same(branch([]), "falsy")
assert_same(branch("a"), "truthy")
assert_same(branch(Truth(False)), "falsy")
assert_same(calls, ["bool"])
del calls[:]
assert_same(branch(Truth(True)), "truthy")
assert_same(calls, ["bool", "bool"])
del calls[:]
assert_same(branch(Sized(0)), "falsy")
assert_same(calls, ["len"])
del calls[:]
assert_raises(ValueError, branch, Broken())
assert_raises(TypeError, branch, Odd())

count = 0
done = Truth(False)
while not done:
    count += 1
    if count == 3:
        done = Truth(True)
assert_same(count, 3)
assert_same(calls, ["bool", "bool", "bool", "bool"])
del calls[:]

values = [0, 1, None, "", "b", Sized(2)]
assert_same([type(v).__name__ for v in values if not v], ["int", "NoneType", "str"])
assert_same(calls, ["len"])
del calls[:]
assert_same(["no" if not v else "yes" for v in (0, 2)], ["no", "yes"])


def guarded(value):
    match value:
        case [x] if not x:
            return "empty one"
        case [x]:
            return "one"
    return "other"


assert_same(guarded([0]), "empty one")
assert_same(guarded([5]), "one")
assert_same(guarded(3), "other")


def combined(a, b):
    if not (a and b):
        return "not both"
    if not a or not b:
        return "never"
    return "both"


assert_same(combined(1, 0), "not both")
assert_same(combined(Truth(True), 1), "both")
assert_same(calls, ["bool", "bool"])
del calls[:]

flag = None
if not flag is None:
    fail("not flag is None")
