# spec: PLS-315 24.2, 26.3.2, 20.1.4
# description: a bytearray's and a set's __reduce__ and __reduce_ex__ call
# the instance's Python __getstate__ for the state, or object's default
# one for an instance dict, whether called as a method, through the type,
# by map() or a generator; its error propagates, nothing returned. Inside
# functions and generators as at module level.
from harness import *
log = []
class B(bytearray):
    def __getstate__(self):
        for _ in (): pass
        log.append(("b", bytes(self)))
        return {"x": 1}
class S(set):
    def __getstate__(self):
        for _ in (): pass
        log.append(("s", sorted(self)))
        return None
class F(frozenset): pass
class Plain(bytearray): pass
class Bad(bytearray):
    def __getstate__(self):
        for _ in (): pass
        log.append(("bad",))
        raise ValueError("no state")
def named(v):
    if isinstance(v, type): return v.__name__
    if isinstance(v, (tuple, list)): return type(v)(named(x) for x in v)
    return v
def run(f):
    del log[:]
    try: result = named(f())
    except ValueError as error: result = ("ValueError", str(error))
    return result, list(log)
def cases():
    b, s, f, p = B(b"ab"), S([2]), F([3]), Plain(b"q")
    f.a, p.y = 1, 2
    def reduces():
        yield b.__reduce__()
        yield s.__reduce__()
    return [run(lambda: b.__reduce__()), run(lambda: b.__reduce_ex__(3)), run(lambda: bytearray.__reduce_ex__(b, 1)),
            run(lambda: s.__reduce__()), run(lambda: set.__reduce__(s)), run(lambda: f.__reduce__()), run(lambda: p.__reduce__()),
            run(lambda: bytearray(b"z").__reduce__()), run(lambda: set().__reduce__()), run(lambda: Bad(b"x").__reduce__()),
            run(lambda: list(map(bytearray.__reduce__, [b, p]))), run(lambda: list(map(set.__reduce__, [s]))),
            run(lambda: list(reduces())), run(lambda: [x[2] for x in map(bytearray.__reduce_ex__, [b, b], [1, 4])])]
def gen():
    yield cases()
expected = [(('B', ('ab', 'latin-1'), {'x': 1}), [('b', b'ab')]),
            (('B', (b'ab',), {'x': 1}), [('b', b'ab')]),
            (('B', ('ab', 'latin-1'), {'x': 1}), [('b', b'ab')]),
            (('S', ([2],), None), [('s', [2])]),
            (('S', ([2],), None), [('s', [2])]),
            (('F', ([3],), {'a': 1}), []),
            (('Plain', ('q', 'latin-1'), {'y': 2}), []),
            (('bytearray', ('z', 'latin-1'), None), []),
            (('set', ([],), None), []),
            (('ValueError', 'no state'), [('bad',)]),
            ([('B', ('ab', 'latin-1'), {'x': 1}), ('Plain', ('q', 'latin-1'), {'y': 2})], [('b', b'ab')]),
            ([('S', ([2],), None)], [('s', [2])]),
            ([('B', ('ab', 'latin-1'), {'x': 1}), ('S', ([2],), None)], [('b', b'ab'), ('s', [2])]),
            ([{'x': 1}, {'x': 1}], [('b', b'ab'), ('b', b'ab')])]
assert_eq(cases(), expected)
assert_eq(next(gen()), expected)
def outer():
    return cases()
assert_eq(outer(), expected)
