# spec: PLS-315 13.2.3, 26.1.2, 26.1.3
# description: Merging a dict into a dict that holds entries, by update(),
# |=, | and a display's **, looks each key up by its stored hash, calling
# no __hash__, and compares it by a Python __eq__, which may loop, with a
# colliding key: an equal key keeps the key stored and takes the value, an
# unequal one is added. A comparison's exception propagates, the entries
# before it merged; a change of the merged dict's size raises RuntimeError
# ("dict mutated during update"); | leaves its operands as they were.
# So does an update() repeated in a loop, its argument made by a call.
# Inside functions as at module level.
from harness import *

log = []

class Key:
    def __init__(self, n, hook=None): self.n = n; self.hook = hook
    def __hash__(self):
        log.append(("hash", self.n))
        return self.n % 2
    def __eq__(self, other):
        for _ in range(2): pass
        log.append(("eq", self.n, other.n))
        if self.hook: self.hook()
        if self.n < 0: raise LookupError(self.n)
        return self.n == other.n
    def __repr__(self): return "K%d" % self.n

def error(f):
    try:
        return f()
    except (LookupError, RuntimeError) as e:
        return type(e).__name__, str(e)

def shown(d): return sorted((k.n, v) for k, v in d.items())

def merges():
    one, three = Key(1), Key(3)
    d, e = {one: "a", three: "b"}, {Key(1): "x", Key(5): "y", Key(3): "z"}
    del log[:]
    out = [d.update(e), shown(d), [k is one for k in d][0]]
    d, e = {Key(1): "a"}, {Key(3): "x"}
    out += [shown(d | e), shown(d)]
    d |= e
    out += [shown(d), shown({**{Key(1): 2}, **e}), shown({Key(7): 0, **e})]
    d = {Key(-1): "bad"}
    out += [error(lambda: d.update({Key(3): 1, Key(4): 2})), shown(d)]
    source = {Key(3): "x"}
    def grow(): source[Key(9)] = 0
    d = {Key(1, grow): "a"}
    out += [error(lambda: d.update(source)), shown(d)]
    return out + [list(log)]

expected = [None, [(1, 'x'), (3, 'z'), (5, 'y')], True, [(1, 'a'), (3, 'x')], [(1, 'a')], [(1, 'a'), (3, 'x')],
            [(1, 2), (3, 'x')], [(3, 'x'), (7, 0)], ('LookupError', '-1'), [(-1, 'bad')],
            ('RuntimeError', 'dict mutated during update'), [(1, 'a'), (3, 'x')],
            [('eq', 1, 1), ('eq', 1, 5), ('eq', 3, 5), ('eq', 1, 3), ('eq', 3, 3), ('hash', 1), ('hash', 3),
             ('eq', 1, 3), ('eq', 1, 3), ('hash', 1), ('eq', 1, 3), ('hash', 7), ('eq', 7, 3), ('hash', -1),
             ('hash', 3), ('hash', 4), ('eq', -1, 3), ('hash', 3), ('hash', 1), ('eq', 1, 3), ('hash', 9),
             ('eq', 3, 9)]]

def repeated():
    d = {Key(1): "a"}
    del log[:]
    for i in range(4):
        d.update(dict([(Key(1), i)]))
    return shown(d), list(log)

assert_eq(repeated(), ([(1, 3)], [('hash', 1), ('eq', 1, 1)] * 4))

def main():
    return merges()

assert_eq(main(), expected)
assert_eq(merges(), expected)
