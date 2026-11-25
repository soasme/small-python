# spec: PLS-315 26.1.2, 26.2
# description: a dict finds a tuple key holding a frozendict, itself or in
# a nested tuple, whose value has a Python __eq__ and object's hash: the
# same value object is the same key by identity, so its __eq__ is never
# called, and an equal-looking key of another instance is absent.
from harness import assert_eq

log = []

class E:
    __hash__ = object.__hash__
    def __eq__(self, other):
        for _ in (): pass
        log.append("eq")
        return self is other

def run():
    e = E()
    d = {(1, frozendict(a=e)): "e", (2, frozendict(b=2)): "p", (3, (frozendict(c=e),)): "n"}
    return [d[(1, frozendict(a=e))], d[(2, frozendict(b=2))], d[(3, (frozendict(c=e),))],
            (1, frozendict(a=E())) in d, (1, frozendict(a=e)) in d]

assert_eq(run(), ["e", "p", "n", False, True])
assert_eq(log, [])
