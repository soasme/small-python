# spec: PLS-315 7.2.4, 7.2.5, 26.1.2, 26.3.2, 23.4
# description: A comparison's reflected method comes first only when the
# right operand's class is a subclass of the left's. A set or frozenset
# compares an instance of the other one's subclass, a dict or frozendict
# one of the other's, and a bytearray one of a bytes subclass, by its own
# method, which answers: the instance's Python reflected method, a
# descriptor's __get__ included, is not called, in an operator, container
# equality and ordering, or min and max; a subclass of the left
# operand's own class still has its reflected method called first.
from harness import assert_eq

log = []

def spin():
    for _ in (): pass

def reflected(name, value):
    def method(self, other):
        spin()
        log.append(name)
        return value
    return method

class Getter:
    def __get__(self, obj, cls):
        log.append("get")
        return lambda other: "got"

class FS(frozenset):
    __eq__ = reflected("FS.eq", "r"); __ge__ = reflected("FS.ge", "r"); __gt__ = reflected("FS.gt", True)
    __le__ = Getter(); __hash__ = frozenset.__hash__
class SS(set):
    __eq__ = reflected("SS.eq", "r"); __ge__ = reflected("SS.ge", "r")
class FD(frozendict):
    __eq__ = reflected("FD.eq", "r"); __hash__ = frozendict.__hash__
class D(dict):
    __eq__ = reflected("D.eq", "r")
class B(bytes):
    __eq__ = reflected("B.eq", "r"); __gt__ = reflected("B.gt", "r"); __hash__ = bytes.__hash__

def run():
    cases = [lambda: set() <= FS(), lambda: set() == FS(), lambda: set() >= FS({1}), lambda: frozenset() <= SS(),
             lambda: frozenset() == SS(), lambda: {} == FD(), lambda: frozendict() == D(), lambda: bytearray(b"a") < B(b"b"),
             lambda: bytearray(b"a") == B(b"a"), lambda: [set()] == [FS()], lambda: (frozenset(),) == (SS(),),
             lambda: [{}] == [FD()], lambda: [set()] < [FS({1})], lambda: [bytearray(b"a")] < [B(b"b")],
             lambda: min([FS({1}), set()]), lambda: max(set(), FS({1})),
             lambda: set() <= SS(), lambda: frozenset() <= FS(), lambda: frozenset() >= FS(), lambda: {} == D(), lambda: b"a" == B(b"a")]
    out = []
    for case in cases:
        log.clear()
        out.append((case(), list(log)))
    return out

expected = [(True, []), (True, []), (False, []), (True, []), (True, []), (True, []), (True, []), (True, []), (True, []),
            (True, []), (True, []), (True, []), (True, []), (True, []), (set(), []), (FS({1}), ["FS.gt"]),
            ("r", ["SS.ge"]), ("r", ["FS.ge"]), ("got", ["get"]), ("r", ["D.eq"]), ("r", ["B.eq"])]
assert_eq(run(), expected)
assert_eq(run(), expected)
