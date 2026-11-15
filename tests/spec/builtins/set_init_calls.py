# spec: PLS-315 26.3.1, 7.5.7
# description: set.__init__ called on a set or a set subclass's instance,
# through super() in a Python __init__, bound or unbound, empties the set,
# then adds the items of its iterable, a generator, a list or an iterator
# over one, each hashed by its Python __hash__ and compared by its Python
# __eq__, both of which may loop, before the next is taken; an exception
# propagates, the items before it kept, as does an unhashable item's
# TypeError, and set.__init__ refuses a frozenset, a second source and a
# keyword. Inside functions as at module level.
from harness import *

log = []

class K:
    def __init__(self, v): self.v = v
    def __hash__(self):
        for _ in range(2): pass
        log.append(("h", self.v))
        if self.v < 0: raise ValueError(self.v)
        return self.v % 2
    def __eq__(self, other):
        for _ in range(2): pass
        log.append(("e", self.v, other.v))
        return self.v == other.v

def gen(*values):
    for v in values:
        log.append(("y", v))
        yield K(v)

class S(set):
    def __init__(self, source):
        log.append("init")
        super().__init__(source)

def vals(s): return sorted(k.v for k in s)

def error(f):
    try:
        return f()
    except (ValueError, TypeError) as e:
        return type(e).__name__, str(e)

def inits():
    del log[:]
    a = S(gen(1, 2, 3))
    b = S([K(4), K(6)])
    out = [type(a).__name__, vals(a), vals(b)]
    a.__init__(iter([K(5), K(7)]))
    s = {K(9)}
    set.__init__(s, [K(1), K(3)])
    out += [vals(a), vals(s), error(lambda: set.__init__(s, gen(2, -1, 4))), vals(s)]
    s.__init__(())
    out += [vals(s), error(lambda: set.__init__(frozenset(), [K(1)])), error(lambda: set.__init__(s, [K(8), []])), vals(s),
            error(lambda: set.__init__(S.__new__(S), [], [])), error(lambda: set.__init__(s, (), x=1)), list(log)]
    return out

expected = ['S',
            [1, 2, 3],
            [4, 6],
            [5, 7],
            [1, 3],
            ('ValueError', '-1'),
            [2],
            [],
            ('TypeError', "descriptor '__init__' requires a 'set' object but received a 'frozenset'"),
            ('TypeError', "cannot use 'list' as a set element (unhashable type: 'list')"),
            [8],
            ('TypeError', 'S expected at most 1 argument, got 2'),
            ('TypeError', 'set() takes no keyword arguments'),
            ['init', ('y', 1), ('h', 1), ('y', 2), ('h', 2), ('y', 3), ('h', 3), ('e', 1, 3),
             'init', ('h', 4), ('h', 6), ('e', 4, 6), 'init', ('h', 5), ('h', 7), ('e', 5, 7),
             ('h', 9), ('h', 1), ('h', 3), ('e', 1, 3), ('y', 2), ('h', 2), ('y', -1), ('h', -1),
             ('h', 8)]]

def main():
    return inits()

assert_eq(main(), expected)
assert_eq(inits(), expected)
