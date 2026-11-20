# spec: PLS-315 26.1.1, 26.2
# description: dict(), dict.update() and frozendict() of an instance whose
# keys a Python __getattr__ gives ask it for keys twice, as the check for
# a mapping and as keys()'s lookup, then call what it gave and merge each
# key by the Python __getitem__; an AttributeError from the first merges
# the instance's pairs instead; other errors, a keys that is not callable
# and errors from keys() or __getitem__ propagate. A native or generator
# keys works too, and inside a generator.
from harness import assert_eq

log = []
class Asked:
    def __init__(self, mode): self.mode = mode
    def __getattr__(self, name):
        for _ in (): pass
        log.append(("ask", name))
        m = self.mode
        if name == "keys":
            if m == "absent": raise AttributeError(name)
            if m == "fails": raise KeyError("ask")
            if m == "second" and sum(1 for e in log if e == ("ask", "keys")) > 1: raise LookupError("second")
            if m == "native": return {"n": 1}.keys
            if m == "notcall": return 5
            if m == "gen": return lambda: (k for k in "ab")
            if m == "keysfail": return lambda: 1/0
            return lambda: ["k", "j"]
        raise AttributeError(name)
    def __iter__(self):
        log.append("iter")
        if self.mode == "absent": return iter([("x", 1)])
        return iter([])
    def __getitem__(self, k):
        for _ in (): pass
        log.append(("get", k))
        if k == "j" and self.mode == "getfail": raise IndexError("get")
        return k * 2
class NoIter:
    def __getattr__(self, name): raise AttributeError(name)
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
CALLS = {"dict": lambda m: dict(Asked(m)), "update": lambda m: (lambda d: (d.update(Asked(m)), d))({"z": 0}),
         "frozendict": lambda m: frozendict(Asked(m))}
CASES = {
    ('plain', 'dict'): ({'k': 'kk', 'j': 'jj'}, [('ask', 'keys'), ('ask', 'keys'), ('get', 'k'), ('get', 'j')]),
    ('plain', 'update'): ((None, {'z': 0, 'k': 'kk', 'j': 'jj'}), [('ask', 'keys'), ('ask', 'keys'), ('get', 'k'), ('get', 'j')]),
    ('plain', 'frozendict'): (frozendict({'k': 'kk', 'j': 'jj'}), [('ask', 'keys'), ('ask', 'keys'), ('get', 'k'), ('get', 'j')]),
    ('absent', 'dict'): ({'x': 1}, [('ask', 'keys'), 'iter']),
    ('absent', 'update'): ((None, {'z': 0, 'x': 1}), [('ask', 'keys'), 'iter']),
    ('absent', 'frozendict'): (frozendict({'x': 1}), [('ask', 'keys'), 'iter']),
    ('fails', 'dict'): (('KeyError', "'ask'"), [('ask', 'keys')]),
    ('fails', 'update'): (('KeyError', "'ask'"), [('ask', 'keys')]),
    ('fails', 'frozendict'): (('KeyError', "'ask'"), [('ask', 'keys')]),
    ('second', 'dict'): (('LookupError', 'second'), [('ask', 'keys'), ('ask', 'keys')]),
    ('second', 'update'): (('LookupError', 'second'), [('ask', 'keys'), ('ask', 'keys')]),
    ('second', 'frozendict'): (('LookupError', 'second'), [('ask', 'keys'), ('ask', 'keys')]),
    ('native', 'dict'): ({'n': 'nn'}, [('ask', 'keys'), ('ask', 'keys'), ('get', 'n')]),
    ('native', 'update'): ((None, {'z': 0, 'n': 'nn'}), [('ask', 'keys'), ('ask', 'keys'), ('get', 'n')]),
    ('native', 'frozendict'): (frozendict({'n': 'nn'}), [('ask', 'keys'), ('ask', 'keys'), ('get', 'n')]),
    ('notcall', 'dict'): (('TypeError', "'int' object is not callable"), [('ask', 'keys'), ('ask', 'keys')]),
    ('notcall', 'update'): (('TypeError', "'int' object is not callable"), [('ask', 'keys'), ('ask', 'keys')]),
    ('notcall', 'frozendict'): (('TypeError', "'int' object is not callable"), [('ask', 'keys'), ('ask', 'keys')]),
    ('gen', 'dict'): ({'a': 'aa', 'b': 'bb'}, [('ask', 'keys'), ('ask', 'keys'), ('get', 'a'), ('get', 'b')]),
    ('gen', 'update'): ((None, {'z': 0, 'a': 'aa', 'b': 'bb'}), [('ask', 'keys'), ('ask', 'keys'), ('get', 'a'), ('get', 'b')]),
    ('gen', 'frozendict'): (frozendict({'a': 'aa', 'b': 'bb'}), [('ask', 'keys'), ('ask', 'keys'), ('get', 'a'), ('get', 'b')]),
    ('keysfail', 'dict'): (('ZeroDivisionError', 'division by zero'), [('ask', 'keys'), ('ask', 'keys')]),
    ('keysfail', 'update'): (('ZeroDivisionError', 'division by zero'), [('ask', 'keys'), ('ask', 'keys')]),
    ('keysfail', 'frozendict'): (('ZeroDivisionError', 'division by zero'), [('ask', 'keys'), ('ask', 'keys')]),
    ('getfail', 'dict'): (('IndexError', 'get'), [('ask', 'keys'), ('ask', 'keys'), ('get', 'k'), ('get', 'j')]),
    ('getfail', 'update'): (('IndexError', 'get'), [('ask', 'keys'), ('ask', 'keys'), ('get', 'k'), ('get', 'j')]),
    ('getfail', 'frozendict'): (('IndexError', 'get'), [('ask', 'keys'), ('ask', 'keys'), ('get', 'k'), ('get', 'j')]),
}
assert_eq(len(CASES), 27)
for (mode, name), expected in CASES.items():
    assert_eq(run(lambda: CALLS[name](mode)), expected, f"{mode} {name}")
assert_eq(run(lambda: dict(NoIter())), (('TypeError', "'NoIter' object is not iterable"), []))
def g():
    yield dict(Asked("plain"))
assert_eq(run(lambda: next(g())), ({'k': 'kk', 'j': 'jj'}, [('ask', 'keys'), ('ask', 'keys'), ('get', 'k'), ('get', 'j')]))
