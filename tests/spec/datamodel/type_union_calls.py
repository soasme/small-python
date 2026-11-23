# spec: PLS-315 20.2.7, 29.5.1
# description: type.__or__ and type.__ror__, called through type, bound to
# a class by __get__, or by a metaclass's super(), make a union of the class and a
# union member, a generic alias hashing its argument's Python __hash__,
# which may loop, or decline other operands with NotImplemented; the
# first is this program's first union. Inside functions and generators
# as at module level.
from harness import *

log = []

class Member:
    def __init__(self, name): self.name = name
    def __eq__(self, other):
        for _ in range(2): pass
        log.append(("eq", self.name))
        return isinstance(other, Member) and other.name == self.name
    def __hash__(self):
        for _ in range(2): pass
        log.append(("hash", self.name))
        return hash(self.name)
    def __repr__(self): return self.name

class Meta(type):
    def __or__(cls, other):
        for _ in range(1): pass
        return ("or", super().__or__(other))

class K(metaclass=Meta): pass

def args(u): return u.__args__ if hasattr(u, "__args__") else u

def run(f, *operands):
    del log[:]
    r = f(*operands)
    return (r if r is NotImplemented or isinstance(r, tuple) and r[0] == "or" and r[1] is NotImplemented else args(r) if not isinstance(r, tuple) else (r[0], args(r[1]))), log[:]

def m(): return list[Member("m")]
def cases():
    return [run(type.__or__, int, m()), run(type.__ror__, int, m()), run(type.__or__.__get__(int), str), run(type.__ror__.__get__(int), str),
            run(type.__or__, int, 1), run(type.__ror__, int, 1), run(K.__or__, int), run(lambda: K | m())]

expected = [((int, m()), [("hash", "m")]), ((m(), int), [("hash", "m")]), ((int, str), []), ((str, int), []),
            (NotImplemented, []), (NotImplemented, []), (("or", (K, int)), []), (("or", (K, m())), [("hash", "m")])]

def gen():
    yield cases()

assert_eq(cases(), expected)
assert_eq(next(gen()), expected)
def main(): return cases()
assert_eq(main(), expected)

# type's | of a value that joins no union is NotImplemented, and then a
# TypeError.
assert_eq([type.__or__(int, 5), type.__ror__(int, 5), type.__or__(int, "x")], [NotImplemented, NotImplemented, NotImplemented])
with assert_raises(TypeError, message="unsupported operand type(s) for |: 'type' and 'int'"):
    int | 5
