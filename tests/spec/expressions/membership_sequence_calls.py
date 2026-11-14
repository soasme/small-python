# spec: PLS-315 7.8.3, 13.10
# description: x in a list or tuple, x itself a tuple, list or dict,
# compares each item v with x as v == x, in order: two sequences compare
# their items pair by pair, v's first, nested sequences in turn, tuples
# of other lengths too, each Python __eq__ called as it is reached and
# which may loop; the first
# equal item stops the search, an identical item matches with no call,
# an instance item calls its own __eq__ with the sequence, and an error
# from __eq__ propagates from the test. Inside functions as at module
# level.
from harness import *

log = []

class Q:
    def __init__(self, v): self.v = v
    def __eq__(self, other):
        for _ in (): pass
        log.append((self.v, other.v if isinstance(other, Q) else type(other).__name__))
        return isinstance(other, Q) and self.v == other.v
    __hash__ = None

def searches():
    out = []
    out.append(((Q(1),) in [(Q(2),), (Q(1),)], log[:])); log.clear()
    out.append(([Q(1)] in [[1], [Q(3)], (Q(1),), [Q(1)]], log[:])); log.clear()
    out.append(((1, Q(1)) not in [(1, Q(1))], log[:])); log.clear()
    out.append(((Q(1), (Q(2),)) in [(Q(1), (Q(3),)), (Q(1), (Q(2),))], log[:])); log.clear()
    out.append(({1: Q(1)} in [{1: Q(2)}, {1: Q(1)}], log[:])); log.clear()
    out.append(((Q(5),) in [Q(5), (Q(6),)], log[:])); log.clear()
    out.append(((Q(1),) in ((Q(9),), 3, (Q(1),)), log[:])); log.clear()
    x = (Q(1),)
    out.append((x in [(Q(2),), x], log[:])); log.clear()
    out.append(((Q(4),) in [(Q(5), 0), (Q(4),)], log[:])); log.clear()
    return out

expected = [
    (True, [(2, 1), (1, 1)]),
    (True, [(1, "int"), (3, 1), (1, 1)]),
    (False, [(1, 1)]),
    (True, [(1, 1), (3, 2), (1, 1), (2, 2)]),
    (True, [(2, 1), (1, 1)]),
    (False, [(5, "tuple"), (6, 5)]),
    (True, [(9, 1), (1, 1)]),
    (True, [(2, 1)]),
    (True, [(5, 4), (4, 4)]),
]
assert_eq(searches(), expected)
log.clear()

class Bad:
    def __eq__(self, other):
        for _ in (): pass
        raise LookupError("eq")
    __hash__ = None

def errors():
    try: (Bad(),) in [(1,), (Bad(),)]
    except LookupError as e: return e.args

assert_eq(errors(), ("eq",))
