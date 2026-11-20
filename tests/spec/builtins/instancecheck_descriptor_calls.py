# spec: PLS-315 19.3.21, 19.3.22
# description: isinstance() and issubclass() read an __instancecheck__ or
# __subclasscheck__ that a descriptor's Python __get__ gives, which may
# loop or raise, for an instance target, one in a tuple or nested tuple,
# and a metaclass's; the hook's result has its truth taken by a Python
# __bool__ or __len__, a tuple going on to its next item when false.
from harness import *

log = []
class D:
    def __init__(s, f, mode=None): s.f = f; s.mode = mode
    def __get__(s, obj, owner):
        for _ in (): pass
        log.append(("get", s.f.__name__, type(obj).__name__))
        if s.mode == "attr": raise AttributeError("gone")
        if s.mode == "key": raise KeyError("k")
        return s.f.__get__(obj, owner)
class Truth:
    def __init__(s, v): s.v = v
    def __bool__(s): log.append("bool"); return s.v
def __instancecheck__(self, x): log.append(("check", x)); return getattr(self, "answer", True)
def __subclasscheck__(self, x): log.append(("sub", x)); return Truth(False)
def mk(mode=None, answer=True):
    X = type("X", (), {"__instancecheck__": D(__instancecheck__, mode), "__subclasscheck__": D(__subclasscheck__, mode)})
    x = X(); x.answer = answer; return x
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def results():
    out = []
    for mode in (None, "attr", "key"):
        x = mk(mode)
        out.append((run(lambda: isinstance(1, x)), run(lambda: issubclass(int, x)), run(lambda: isinstance(1, (str, x))), run(lambda: issubclass(int, ((x,), str)))))
    out.append((run(lambda: isinstance(1, mk(None, 0))), run(lambda: isinstance(1, mk(None, Truth(True)))), run(lambda: isinstance(1, (mk(None, []), mk(None, [1]))))))
    class M(type):
        __instancecheck__ = D(lambda cls, x: x == 5)
    class K(metaclass=M): pass
    out.append(run(lambda: (isinstance(5, K), isinstance(6, K), isinstance(K(), K))))
    def inside():
        for _ in (): pass
        return isinstance(1, mk()), issubclass(int, (mk(),))
    out.append(run(inside))
    return out

expected = [
    ((True, [('get', '__instancecheck__', 'X'), ('check', 1)]), (False, [('get', '__subclasscheck__', 'X'), ('sub', int), 'bool']), (True, [('get', '__instancecheck__', 'X'), ('check', 1)]), (False, [('get', '__subclasscheck__', 'X'), ('sub', int), 'bool'])),
    ((('AttributeError', 'gone'), [('get', '__instancecheck__', 'X')]), (('AttributeError', 'gone'), [('get', '__subclasscheck__', 'X')]), (('AttributeError', 'gone'), [('get', '__instancecheck__', 'X')]), (('AttributeError', 'gone'), [('get', '__subclasscheck__', 'X')])),
    ((('KeyError', "'k'"), [('get', '__instancecheck__', 'X')]), (('KeyError', "'k'"), [('get', '__subclasscheck__', 'X')]), (('KeyError', "'k'"), [('get', '__instancecheck__', 'X')]), (('KeyError', "'k'"), [('get', '__subclasscheck__', 'X')])),
    ((False, [('get', '__instancecheck__', 'X'), ('check', 1)]), (True, [('get', '__instancecheck__', 'X'), ('check', 1), 'bool']), (True, [('get', '__instancecheck__', 'X'), ('check', 1), ('get', '__instancecheck__', 'X'), ('check', 1)])),
    (((True, False, True), [('get', '<lambda>', 'M'), ('get', '<lambda>', 'M')])),
    (((True, False), [('get', '__instancecheck__', 'X'), ('check', 1), ('get', '__subclasscheck__', 'X'), ('sub', int), 'bool'])),
]

assert_eq(results(), expected)
