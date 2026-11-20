# spec: PLS-315 26.1.1, 13.2.3
# description: dict(), dict.update(), a ** display and frozendict() of a
# mapping whose keys() returns no iterable raise TypeError naming the
# mapping's class by its qualified name, after its module unless that is
# builtins or __main__, as "<name>.keys() must return an iterable, not
# <type>"; a function's keys() is named "function"; and so inside a
# generator.
from harness import assert_eq

def make():
    class Local:
        def keys(self): return 5
        def __getitem__(self, k): return k
    return Local
class Top:
    def keys(self): return 5
    def __getitem__(self, k): return k
class Outer:
    class Inner(Top): pass
def f(): pass
f.keys = lambda: 5
Mod = type('Mod', (Top,), {'__module__': 'pkg.mod'})
Named = type('Named', (Top,), {'__qualname__': 'Some.Named'})
def messages():
    seen = []
    for src in (make()(), Top(), Outer.Inner(), Mod(), Named()):
        for build in (lambda s: dict(s), lambda s: {}.update(s), lambda s: {**s}, lambda s: frozendict(s)):
            try: build(src)
            except TypeError as e: seen.append(str(e))
    for build in (lambda s: dict(s), lambda s: {**s}):
        try: build(f)
        except TypeError as e: seen.append(str(e))
    return seen
def g():
    try: yield dict(make()())
    except TypeError as e: yield str(e)
EXPECTED = [
    'make.<locals>.Local.keys() must return an iterable, not int',
    'make.<locals>.Local.keys() must return an iterable, not int',
    'make.<locals>.Local.keys() must return an iterable, not int',
    'make.<locals>.Local.keys() must return an iterable, not int',
    'Top.keys() must return an iterable, not int',
    'Top.keys() must return an iterable, not int',
    'Top.keys() must return an iterable, not int',
    'Top.keys() must return an iterable, not int',
    'Outer.Inner.keys() must return an iterable, not int',
    'Outer.Inner.keys() must return an iterable, not int',
    'Outer.Inner.keys() must return an iterable, not int',
    'Outer.Inner.keys() must return an iterable, not int',
    'pkg.mod.Mod.keys() must return an iterable, not int',
    'pkg.mod.Mod.keys() must return an iterable, not int',
    'pkg.mod.Mod.keys() must return an iterable, not int',
    'pkg.mod.Mod.keys() must return an iterable, not int',
    'Some.Named.keys() must return an iterable, not int',
    'Some.Named.keys() must return an iterable, not int',
    'Some.Named.keys() must return an iterable, not int',
    'Some.Named.keys() must return an iterable, not int',
    'function.keys() must return an iterable, not int',
    'function.keys() must return an iterable, not int',
]
assert_eq(messages(), EXPECTED)
assert_eq(repr(list(g())), "['make.<locals>.Local.keys() must return an iterable, not int']")
