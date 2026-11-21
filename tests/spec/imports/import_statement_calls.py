# spec: PLS-315 17.4.3
# description: an import statement's __import__ hook, a from-import's
# attribute reads, a star's __all__ and its __getitem__, an import-as's
# reads of each dotted part, and a namespace mapping's __setitem__ each run
# once, in order, as Python code; a missing name raises ImportError naming
# the object's __name__ when a str, and the module's file; inside
# generators and comprehensions too.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
log = []
Module = type(__import__("builtins"))
def hook_for(obj):
    def hook(name, g=None, l=None, fromlist=(), level=0):
        for _ in (): pass
        log.append(('import', name, fromlist, level)); return obj
    return hook
def run(src, obj, ns=None):
    del log[:]
    scope = {"__builtins__": {"__import__": hook_for(obj)}}
    target = scope if ns is None else ns
    try: exec(src, scope, target); r = sorted(k for k in target if k != "__builtins__")
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
class Dyn(Module):
    def __getattr__(self, name):
        for _ in (): pass
        log.append(('getattr', name))
        if name == "__all__": return ["z", "w"]
        if name in ("z", "w", "q"): return 1
        raise AttributeError(name)
class Letters:
    def __getitem__(self, i):
        for _ in (): pass
        log.append(('item', i))
        if i < 2: return "ab"[i]
        raise IndexError
class Listed:
    __all__ = Letters()
    a, b, c = 1, 2, 3
class Upper(dict):
    def __setitem__(self, key, value):
        for _ in (): pass
        log.append(('set', key)); super().__setitem__(key.upper(), value)
class BadItem:
    def __getitem__(self, i):
        raise KeyError(i)
class Holder: __all__ = BadItem()
class Prop:
    @property
    def x(self):
        for _ in (): pass
        log.append('prop'); return 7
    @property
    def boom(self): raise ValueError('p')
mm = Module("mm"); mm.k, mm._h = 1, 2
cases = [("from x import *", Dyn("d")), ("from x import q, z as zz", Dyn("d")), ("from x import nope", Dyn("d")), ("from x import *", Listed),
         ("from x import *", mm), ("from x import x, x as y", Prop()), ("from x import boom", Prop()), ("from x import *", Holder),
         ("import a.b as c", Prop()), ("import a, b", mm), ("from .x import k", mm), ("from x import nope", mm), ("import a.k as c", mm)]
for src, obj in cases: emit(repr(run(src, obj)))
emit(repr(run("from x import *", mm, Upper())), repr(run("from x import k, _h", mm, Upper())))
def g():
    yield run("from x import *", Dyn("d"))
    yield run("from x import q", Dyn("d"), Upper())
emit(repr(list(g())))
emit(repr([run("from x import *", Listed) for _ in (0,)]))
def f():
    from builtins import len as L
    import builtins as B
    return L, B.__name__
emit(f()[1])
class Named: __name__ = 5
class Text: __name__ = 'tx'
fm = Module("fm"); fm.__file__ = "/f.py"
def err(src, obj):
    try: exec(src, {"__builtins__": {"__import__": hook_for(obj)}})
    except ImportError as e: return (str(e), e.name, e.path, e.name_from)
for o in (Named, Text, Prop(), fm, Dyn("d")): emit(repr(err("from x import nope", o)), repr(err("import x.nope as n", o)))
class Deep(Module):
    def __getattr__(self, name):
        for _ in (): pass
        log.append(('deep', name))
        if name == 'boom': raise KeyError(name)
        if name == 'stop': raise AttributeError(name)
        return Deep(self.__name__ + '.' + name)
for src in ("import a.b.c as d", "import a.b as d, a as e", "import a.stop.c as d", "import a.boom as d", "import a.b.stop as d"):
    r = run(src, Deep("a"))
    emit(repr(r[0]) if isinstance(r[0], tuple) else r[0], r[1])
emit(repr(run("import a.b.c as d", Deep("a"), Upper())))
EXPECTED = [
    "(['w', 'z'], [('import', 'x', ('*',), 0), ('getattr', '__all__'), ('getattr', 'z'), ('getattr', 'w')])",
    "(['q', 'zz'], [('import', 'x', ('q', 'z'), 0), ('getattr', 'q'), ('getattr', 'z')])",
    '((\'ImportError\', "cannot import name \'nope\' from \'d\' (unknown location)"), [(\'import\', \'x\', (\'nope\',), 0), (\'getattr\', \'nope\')])',
    "(['a', 'b'], [('import', 'x', ('*',), 0), ('item', 0), ('item', 1), ('item', 2)])",
    "(['k'], [('import', 'x', ('*',), 0)])",
    "(['x', 'y'], [('import', 'x', ('x', 'x'), 0), 'prop', 'prop'])",
    "(('ValueError', 'p'), [('import', 'x', ('boom',), 0)])",
    "(('KeyError', '0'), [('import', 'x', ('*',), 0)])",
    '((\'ImportError\', "cannot import name \'b\' from \'<unknown module name>\' (unknown location)"), [(\'import\', \'a.b\', None, 0)])',
    "(['a', 'b'], [('import', 'a', None, 0), ('import', 'b', None, 0)])",
    "(['k'], [('import', 'x', ('k',), 1)])",
    '((\'ImportError\', "cannot import name \'nope\' from \'mm\' (unknown location)"), [(\'import\', \'x\', (\'nope\',), 0)])',
    "(['c'], [('import', 'a.k', None, 0)])",
    "(['K'], [('import', 'x', ('*',), 0), ('set', 'k')]) (['K', '_H'], [('import', 'x', ('k', '_h'), 0), ('set', 'k'), ('set', '_h')])",
    "[(['w', 'z'], [('import', 'x', ('*',), 0), ('getattr', '__all__'), ('getattr', 'z'), ('getattr', 'w')]), (['Q'], [('import', 'x', ('q',), 0), ('getattr', 'q'), ('set', 'q')])]",
    "[(['a', 'b'], [('import', 'x', ('*',), 0), ('item', 0), ('item', 1), ('item', 2)])]",
    'builtins',
    '("cannot import name \'nope\' from \'Named\' (unknown location)", \'Named\', None, \'nope\') ("cannot import name \'nope\' from \'Named\' (unknown location)", \'Named\', None, \'nope\')',
    '("cannot import name \'nope\' from \'Text\' (unknown location)", \'Text\', None, \'nope\') ("cannot import name \'nope\' from \'Text\' (unknown location)", \'Text\', None, \'nope\')',
    '("cannot import name \'nope\' from \'<unknown module name>\' (unknown location)", None, None, \'nope\') ("cannot import name \'nope\' from \'<unknown module name>\' (unknown location)", None, None, \'nope\')',
    '("cannot import name \'nope\' from \'fm\' (/f.py)", \'fm\', \'/f.py\', \'nope\') ("cannot import name \'nope\' from \'fm\' (/f.py)", \'fm\', \'/f.py\', \'nope\')',
    '("cannot import name \'nope\' from \'d\' (unknown location)", \'d\', None, \'nope\') ("cannot import name \'nope\' from \'d\' (unknown location)", \'d\', None, \'nope\')',
    "['d'] [('import', 'a.b.c', None, 0), ('deep', 'b'), ('deep', 'c')]",
    "['d', 'e'] [('import', 'a.b', None, 0), ('deep', 'b'), ('import', 'a', None, 0)]",
    '(\'ImportError\', "cannot import name \'stop\' from \'a\' (unknown location)") [(\'import\', \'a.stop.c\', None, 0), (\'deep\', \'stop\')]',
    '(\'KeyError\', "\'boom\'") [(\'import\', \'a.boom\', None, 0), (\'deep\', \'boom\')]',
    '(\'ImportError\', "cannot import name \'stop\' from \'a.b\' (unknown location)") [(\'import\', \'a.b.stop\', None, 0), (\'deep\', \'b\'), (\'deep\', \'stop\')]',
    "(['D'], [('import', 'a.b.c', None, 0), ('deep', 'b'), ('deep', 'c'), ('set', 'd')])",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
