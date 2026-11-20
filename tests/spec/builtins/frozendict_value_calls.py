# spec: PLS-315 26.2, 26.3.4, 26.1.2
# description: hashing a frozendict hashes its values, in order, by their
# Python __hash__, nested in tuples and frozendicts either way, keeping the
# hash once complete; == of frozendicts, or of a frozendict and a dict,
# compares the values of each key by their Python __eq__; lookups of a
# frozendict key in a dict or set hash it so and compare it with an equal
# stored key so; a failing __hash__ or __eq__ propagates.
from harness import *

log = []
class H:
    def __init__(self, n, bad=None):
        self.n, self.bad = n, bad
    def __hash__(self):
        for _ in (): pass
        log.append(("h", self.n))
        if self.bad == "raise": raise ValueError(self.n)
        if self.bad == "str": return "x"
        return 7
    def __eq__(self, other):
        for _ in (): pass
        log.append(("e", self.n))
        if self.bad == "raise": raise ValueError(self.n)
        if self.bad == "unequal": return False
        return isinstance(other, H)
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, list(log)
def made(base):
    return frozendict({1: H(base), 2: (H(base + 1), 3), 3: frozendict({4: H(base + 2)})})
def gen():
    yield hash(frozendict({1: H(40)})) == hash(frozendict({1: H(41)}))
    yield frozendict({1: H(42)}) == frozendict({1: H(43)})
    yield frozendict({1: H(44)}) in {frozendict({1: H(45)})}
assert_eq(run(lambda: hash(made(0)) == hash(made(10))), (True, [('h', 0), ('h', 1), ('h', 2), ('h', 10), ('h', 11), ('h', 12)]))
assert_eq(run(lambda: (lambda f: (hash(f), hash(f))[0])(made(0)) == hash(made(10))), (True, [('h', 0), ('h', 1), ('h', 2), ('h', 10), ('h', 11), ('h', 12)]))
assert_eq(run(lambda: hash((1, frozendict({1: H(5)}), H(6))) == hash((1, frozendict({1: H(7)}), H(8)))), (True, [('h', 5), ('h', 6), ('h', 7), ('h', 8)]))
assert_eq(run(lambda: hash(frozendict({1: H(9, 'raise')}))), (('ValueError', '9'), [('h', 9)]))
assert_eq(run(lambda: hash(frozendict({1: H(10, 'str')}))), (('TypeError', '__hash__ method should return an integer'), [('h', 10)]))
assert_eq(run(lambda: hash(frozendict({1: [1]}))), (('TypeError', "unhashable type: 'list'"), []))
assert_eq(run(lambda: hash(frozendict({1: H(11), 2: [H(12)]}))), (('TypeError', "unhashable type: 'list'"), [('h', 11)]))
assert_eq(run(lambda: hash(frozendict()) == hash(frozenset())), (True, []))
assert_eq(run(lambda: made(0) == made(10)), (True, [('e', 0), ('e', 1), ('e', 2)]))
assert_eq(run(lambda: made(0) != made(10)), (False, [('e', 0), ('e', 1), ('e', 2)]))
assert_eq(run(lambda: made(0) == dict(made(10))), (True, [('e', 0), ('e', 1), ('e', 2)]))
assert_eq(run(lambda: dict(made(0)) == made(10)), (True, [('e', 0), ('e', 1), ('e', 2)]))
assert_eq(run(lambda: frozendict({1: H(20, 'unequal')}) == frozendict({1: H(21)})), (False, [('e', 20)]))
assert_eq(run(lambda: frozendict({1: H(22, 'raise')}) == frozendict({1: H(23)})), (('ValueError', '22'), [('e', 22)]))
assert_eq(run(lambda: frozendict({1: H(24)}) == frozendict({2: H(25)})), (False, []))
assert_eq(run(lambda: frozendict({1: H(26)}) == frozendict({1: H(27), 2: 3})), (False, []))
assert_eq(run(lambda: (made(0),) == (made(10),)), (True, [('e', 0), ('e', 1), ('e', 2)]))
assert_eq(run(lambda: [frozendict({1: H(28)})] == [frozendict({1: H(29)})]), (True, [('e', 28)]))
assert_eq(run(lambda: {made(0): 1}[made(10)]), (1, [('h', 0), ('h', 1), ('h', 2), ('h', 10), ('h', 11), ('h', 12), ('e', 0), ('e', 1), ('e', 2)]))
assert_eq(run(lambda: made(10) in {made(0)}), (True, [('h', 0), ('h', 1), ('h', 2), ('h', 10), ('h', 11), ('h', 12), ('e', 0), ('e', 1), ('e', 2)]))
assert_eq(run(lambda: made(10) in [made(0)]), (True, [('e', 0), ('e', 1), ('e', 2)]))
assert_eq(run(lambda: len({made(0), made(10)})), (1, [('h', 0), ('h', 1), ('h', 2), ('h', 10), ('h', 11), ('h', 12), ('e', 0), ('e', 1), ('e', 2)]))
assert_eq(run(lambda: list(dict.fromkeys([made(0)]).values())), ([None], [('h', 0), ('h', 1), ('h', 2)]))
assert_eq(run(lambda: len(set([frozendict({1: H(30)})]))), (1, [('h', 30)]))
assert_eq(run(lambda: list(dict([(frozendict({1: H(31)}), 1)]).values())), ([1], [('h', 31)]))
assert_eq(run(lambda: list({frozendict({1: H(32)}): 2}.values())), ([2], [('h', 32)]))
assert_eq(run(lambda: {frozendict({1: H(33, 'unequal')}): 1}.get(frozendict({1: H(34)}), 'absent')), ('absent', [('h', 33), ('h', 34), ('e', 33)]))
assert_eq(run(lambda: list(gen())), ([True, True, True], [('h', 40), ('h', 41), ('e', 42), ('h', 45), ('h', 44), ('e', 45)]))
