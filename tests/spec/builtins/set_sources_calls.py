# spec: PLS-315 26.3.2
# description: union, intersection, difference and their updates given
# several iterables that are not sets take each in turn: an item's Python
# __hash__ and __eq__, which may loop, are called as it is added to,
# looked up in or discarded from the result so far, an intersection's
# next source searching the previous intersection; intersection_update
# changes the set only at the end. A source's error stops the method,
# later sources unread, inside generators as at module level; so with
# more sources.
from harness import *

log = []

class K:
    def __init__(self, v): self.v = v
    def __hash__(self):
        for _ in range(2): pass
        log.append(("hash", self.v))
        if self.v == "bad": raise LookupError("hash")
        return hash(self.v) & 3
    def __eq__(self, o):
        for _ in range(2): pass
        log.append(("eq", self.v, getattr(o, "v", o)))
        return isinstance(o, K) and self.v == o.v
    def __repr__(self): return "K(%r)" % (self.v,)

def items(*vs):
    for v in vs: yield K(v)

class Watch(K):
    __hash__ = K.__hash__
    def __eq__(self, o):
        log.append(("len", len(target)))
        return K.__eq__(self, o)

def values(s): return sorted(k.v for k in s)

def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = type(e).__name__ + ": " + str(e)
    return r, list(log)

def results():
    global target
    s = {K(1), K(2), K(5)}
    del log[:]
    out = [run(lambda: values(s.union([K(1), K(3)], (K(3),), items(4)))),
           run(lambda: values(s.intersection([K(1), K(2)], items(2, 9)))),
           run(lambda: values(s.difference([K(1)], items(5), [K(7)]))),
           run(lambda: values(frozenset(s).union(items(8), [K(1)]))),
           run(lambda: s.union([K(6)], [K("bad")], items(0)))]
    t = {K(1), K(2), K(3)}
    target = t
    del log[:]
    out.append(run(lambda: (t.intersection_update([Watch(1), Watch(2)], [Watch(2)]), values(t))))
    target = t = {K(1), K(2)}
    del log[:]
    out.append(run(lambda: (t.intersection_update([Watch(1)], [Watch(1)], [Watch(1)], [Watch(1)]), [e[1] for e in log if e[0] == "len"], values(t))))
    u = {K(1)}
    del log[:]
    out.append(run(lambda: (u.update(items(2), [K(1)]), u.difference_update([K(2)], [K(9)]), values(u))))
    return out

expected = [
    ([1, 2, 3, 4, 5], [("hash", 1), ("eq", 1, 1), ("hash", 3), ("hash", 3), ("eq", 3, 3), ("hash", 4)]),
    ([2], [("hash", 1), ("eq", 1, 1), ("hash", 2), ("eq", 2, 2), ("hash", 2), ("eq", 2, 2), ("hash", 9), ("eq", 1, 9)]),
    ([2], [("hash", 1), ("eq", 1, 1), ("hash", 5), ("eq", 5, 5), ("hash", 7)]),
    ([1, 2, 5, 8], [("hash", 8), ("hash", 1), ("eq", 1, 1)]),
    ("LookupError: hash", [("hash", 6), ("eq", 2, 6), ("hash", "bad")]),
    ((None, [2]), [("hash", 1), ("len", 3), ("eq", 1, 1), ("hash", 2), ("len", 3), ("eq", 2, 2), ("hash", 2), ("len", 3), ("eq", 2, 2)]),
    ((None, [2, 2, 2, 2], [1]), [("hash", 1), ("len", 2), ("eq", 1, 1), ("hash", 1), ("len", 2), ("eq", 1, 1),
                                  ("hash", 1), ("len", 2), ("eq", 1, 1), ("hash", 1), ("len", 2), ("eq", 1, 1)]),
    ((None, None, [1]), [("hash", 2), ("hash", 1), ("eq", 1, 1), ("hash", 2), ("eq", 2, 2), ("hash", 9), ("eq", 1, 9)]),
]
assert_eq(results(), expected)

def gen():
    yield results()
assert_eq(next(gen()), expected)
