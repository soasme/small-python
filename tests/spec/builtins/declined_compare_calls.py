# spec: PLS-315 7.2.4, 25.5.3, 26.6
# description: once a list's or tuple's subclass's Python comparison
# returns NotImplemented, the builtin's own method compares the two
# sequences' items, whose Python __eq__ and orderings run in turn; a
# mappingproxy compares its mapping, as the reflected operand of a
# declining __eq__, by its own __eq__ and __ne__, and tests membership by
# the mapping's keys' Python __hash__ and __eq__. Inside functions and
# generators as at module level.
from harness import *

log = []
class V:
    def __init__(self, v): self.v = v
    def __hash__(self):
        for _ in (): pass
        log.append(("hash", self.v))
        return 1
    def __eq__(self, o):
        for _ in (): pass
        log.append(("eq", self.v, getattr(o, "v", o)))
        return isinstance(o, V) and self.v == o.v
    def __lt__(self, o):
        for _ in (): pass
        log.append(("lt", self.v, o.v))
        return self.v < o.v
class L(list):
    def __eq__(self, o):
        for _ in (): pass
        log.append("L.eq")
        return NotImplemented
    def __lt__(self, o):
        for _ in (): pass
        log.append("L.lt")
        return NotImplemented
class T(tuple):
    def __gt__(self, o):
        for _ in (): pass
        log.append("T.gt")
        return NotImplemented
class E:
    def __eq__(self, o):
        for _ in (): pass
        log.append("E.eq")
        return NotImplemented
proxy = type(type.__dict__)({V(1): "a", "k": V(2)})

def run(f):
    del log[:]
    try: r = f()
    except TypeError as e: r = "TypeError"
    return r, list(log)

def cases():
    return [run(lambda: L([V(1), V(2)]) < L([V(1), V(3)])),
            run(lambda: [V(1)] == L([V(1)])),
            run(lambda: L([V(1)]) != [V(2)]),
            run(lambda: (V(1), V(3)) > T((V(1), V(2)))),
            run(lambda: E() == proxy),
            run(lambda: proxy.__eq__({V(1): "a", "k": V(2)})),
            run(lambda: proxy.__ne__({V(1): "a", "k": V(3)})),
            run(lambda: proxy.__contains__(V(1))),
            run(lambda: proxy.__contains__(V(5)))]

expected = [(True, ['L.lt', ('eq', 1, 1), ('eq', 3, 2), ('lt', 2, 3)]),
            (True, ['L.eq', ('eq', 1, 1)]),
            (True, [('eq', 1, 2)]),
            (True, [('eq', 1, 1), ('eq', 2, 3), ('lt', 2, 3)]),
            (False, ['E.eq', 'E.eq']),
            (True, [('hash', 1), ('eq', 1, 1), ('eq', 2, 2)]),
            (True, [('hash', 1), ('eq', 1, 1), ('eq', 2, 3)]),
            (True, [('hash', 1), ('eq', 1, 1)]),
            (False, [('hash', 5), ('eq', 1, 5)])]
assert_eq(cases(), expected)

def gen():
    yield cases()
assert_eq(next(gen()), expected)
