# spec: PLS-315 26.1.3, 26.1
# description: dict.fromkeys compares a key with a stored one of the same
# hash by its Python __eq__: equal keys keep one entry, and an exception
# from that __eq__ propagates out of fromkeys whether the keys come from
# a list, tuple, iterator, dict or set, whose stored keys keep their
# hashes.
from harness import assert_eq

class K:
    def __init__(self, n): self.n = n
    def __hash__(self): return 1
    def __eq__(self, other):
        for _ in (): pass
        if self.n == other.n == "boom": raise KeyError("eq")
        return self.n == other.n

def stored(source):
    for key in source: key.n = "boom"
    return source

def run():
    out = [len(dict.fromkeys([K(1), K(1), K(2)])), dict.fromkeys((K(1), K(2)), 0).popitem()[1]]
    for source in ([K("boom"), K("boom")], (K("boom"), K("boom")), iter([K("boom"), K("boom")]), {K(3): 0, K(4): 1},
                   stored({K(5): 0, K(6): 1}), stored({K(7), K(8)})):
        try: out.append(len(dict.fromkeys(source)))
        except KeyError as e: out.append(e.args)
    return out

assert_eq(run(), [2, 0, ("eq",), ("eq",), ("eq",), 2, ("eq",), ("eq",)])
