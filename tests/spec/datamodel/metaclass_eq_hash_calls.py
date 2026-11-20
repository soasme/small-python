# spec: PLS-315 7.2.4, 7.2.5, 7.5.7, 25.5.3, 26.1.2, 26.1.3, 26.3.2
# description: classes whose metaclass defines a Python __eq__ and
# __hash__ compare and hash by them wherever an instance's would: in list
# and tuple membership, count, index and equality, in set and dict
# displays, subscriptions, membership, methods and equality, and in
# hash() of a tuple; each __hash__ is called once per hashing, each
# __eq__ only for a matching hash or a sequence item, in order. An
# __eq__ returning NotImplemented falls back to identity.
from harness import *

log = []
class M(type):
    def __eq__(self, other):
        for _ in (): pass
        log.append(("eq", self.__name__, getattr(other, "__name__", other)))
        return self.__name__ == getattr(other, "__name__", None)
    def __hash__(self):
        for _ in (): pass
        log.append(("hash", self.__name__))
        return 1

A = M("A", (), {}); A2 = M("A", (), {}); B = M("B", (), {})

def sequences():
    del log[:]
    r = [A2 in [B, A], A2 in (int, B), [A] == [A2], [B, A].index(A2), [A, B].count(A2), max([A, A2], key=id) in (A, A2)]
    return r, list(log)

def maps():
    del log[:]
    s = {B, A}
    d = {B: 1, A: 2}
    r = [A2 in s, s == {A2, B}, d[A2], d.get(A2), A2 in d, {A: 1} == {A2: 1}, {(A, 1): 2}[(A2, 1)], hash((A, 1)) == hash((A2, 1))]
    d[A2] = 3; r.append(d[A]); del d[A2]; r.append(len(d))
    s.add(A2); s.discard(A2); r.append(len(s))
    r.append(d.setdefault(B, 9)); r.append(d.pop(B))
    r.extend([A == A2, B != A, len(set([(A, 1), (A2, 1)])), len({x for x in [(1, A), (1, A2)]})])
    return r, list(log)

class N(type):
    def __eq__(self, other):
        for _ in (): pass
        log.append(("N.eq", self.__name__))
        return NotImplemented
C = N("C", (), {}); D = N("D", (), {})

def declined():
    del log[:]
    return [C == D, C == C, C != D, C in [D], [C] == [D]], list(log)

assert_eq(sequences(), ([True, False, True, 1, 1, True], [
    ('eq', 'B', 'A'), ('eq', 'A', 'A'), ('eq', 'A', 'int'), ('eq', 'B', 'A'), ('eq', 'A', 'A'),
    ('eq', 'B', 'A'), ('eq', 'A', 'A'), ('eq', 'A', 'A'), ('eq', 'B', 'A'), ('eq', 'A', 'A')]))
assert_eq(maps(), ([True, True, 2, 2, True, True, 2, True, 3, 1, 1, 1, 1, True, True, 1, 1], [
    ('hash', 'B'), ('hash', 'A'), ('eq', 'B', 'A'), ('hash', 'B'), ('hash', 'A'), ('eq', 'B', 'A'),
    ('hash', 'A'), ('eq', 'B', 'A'), ('eq', 'A', 'A'), ('hash', 'A'), ('hash', 'B'),
    ('eq', 'A', 'B'), ('eq', 'A', 'B'), ('eq', 'A', 'A'), ('hash', 'A'), ('eq', 'B', 'A'),
    ('eq', 'A', 'A'), ('hash', 'A'), ('eq', 'B', 'A'), ('eq', 'A', 'A'), ('hash', 'A'),
    ('eq', 'B', 'A'), ('eq', 'A', 'A'), ('hash', 'A'), ('hash', 'A'), ('eq', 'A', 'A'),
    ('hash', 'A'), ('hash', 'A'), ('eq', 'A', 'A'), ('hash', 'A'), ('hash', 'A'), ('hash', 'A'),
    ('eq', 'B', 'A'), ('eq', 'A', 'A'), ('hash', 'A'), ('eq', 'B', 'A'), ('hash', 'A'),
    ('eq', 'B', 'A'), ('eq', 'A', 'A'), ('hash', 'A'), ('eq', 'B', 'A'), ('eq', 'A', 'A'),
    ('hash', 'A'), ('eq', 'B', 'A'), ('eq', 'A', 'A'), ('hash', 'B'), ('hash', 'B'),
    ('eq', 'A', 'A'), ('eq', 'B', 'A'), ('hash', 'A'), ('hash', 'A'), ('eq', 'A', 'A'),
    ('hash', 'A'), ('hash', 'A'), ('eq', 'A', 'A')]))
assert_eq(declined(), ([False, True, True, False, False], [
    ('N.eq', 'C'), ('N.eq', 'D'), ('N.eq', 'C'), ('N.eq', 'C'), ('N.eq', 'C'), ('N.eq', 'D'),
    ('N.eq', 'D'), ('N.eq', 'C'), ('N.eq', 'C'), ('N.eq', 'D')]))
