# spec: PLS-315 27.1.3, 7.5.1, 7.3.2
# description: a callable iterator tests the truth of sentinel == result
# by ToBoolean: a descriptor __bool__ whose read raises AttributeError is
# absent (LookupSpecialMaybe), so __len__, itself possibly a descriptor,
# decides, or the result is true without one; a descriptor __bool__'s
# read gives the method called. Both __eq__ declining falls back to
# identity, and a __bool__ call's binding error propagates. As list(),
# map() and a for loop consume it.
from harness import *

log = []

class Gone:
    def __get__(self, o, t=None):
        log.append("get")
        raise AttributeError("gone")

class LenGetter:
    def __get__(self, o, t=None):
        log.append("getlen")
        return lambda: (log.append("len"), o.n)[1]

class BoolGetter:
    def __get__(self, o, t=None):
        log.append("getbool")
        return lambda: o.n == 1

class Absent:
    __bool__ = Gone()
    def __init__(self, n): self.n = n
    def __len__(self):
        log.append("len")
        return self.n

class AbsentLenGetter(Absent):
    __len__ = LenGetter()

class ByGetter(Absent):
    __bool__ = BoolGetter()

class NoLen:
    __bool__ = Gone()
    def __init__(self, n): pass

def consumed(cls):
    class Stop:
        def __eq__(self, other): return cls(other == 2)
    runs = []
    for consume in (list, lambda it: list(map(str, it))):
        log.clear()
        items = iter([1, 2, 3])
        runs.append((consume(iter(lambda: next(items), Stop())), log[:]))
    log.clear()
    items = iter([1, 2, 3])
    for x in iter(lambda: next(items), Stop()):
        log.append(x)
    return runs + [log[:]]

assert_eq(consumed(Absent), [([1], ["get", "len", "get", "len"]), (["1"], ["get", "len", "get", "len"]),
                             ["get", "len", 1, "get", "len"]])
assert_eq(consumed(AbsentLenGetter), [([1], ["get", "getlen", "len"] * 2), (["1"], ["get", "getlen", "len"] * 2),
                                      ["get", "getlen", "len", 1, "get", "getlen", "len"]])
assert_eq(consumed(ByGetter), [([1], ["getbool"] * 2), (["1"], ["getbool"] * 2), ["getbool", 1, "getbool"]])
assert_eq(consumed(NoLen), [([], ["get"]), ([], ["get"]), ["get"]])

class Declines:
    def __eq__(self, other):
        log.append("declines")
        return NotImplemented

class Other:
    def __eq__(self, other):
        log.append("other")
        return NotImplemented

log.clear()
items = iter([Other(), Other()])
assert_eq((len(list(iter(lambda: next(items), Declines()))), log), (2, ["declines", "other"] * 2))

class WrongBool:
    def __bool__(self, extra): return True

class StopWrong:
    def __eq__(self, other): return WrongBool()

assert_raises(TypeError, lambda: list(iter(lambda: 1, StopWrong())),
              message="WrongBool.__bool__() missing 1 required positional argument: 'extra'")
