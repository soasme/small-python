# spec: PLS-315 21.4.1
# description: an exception group of a custom sequence takes its Python
# __repr__ first, which may loop, must return a str and may raise, then a
# tuple of its items through its Python __getitem__; its repr keeps the
# text saved, however the sequence or args change. A subclass's Python
# __init__ runs after, and a Python __new__ calling super().__new__ works
# alike.
from harness import *

log = []
class Seq:
    def __init__(s, items, rep="Seq(...)"): s.items, s.rep = list(items), rep
    def __len__(s): return len(s.items)
    def __getitem__(s, i):
        for _ in (): pass
        log.append(("get", i))
        return s.items[i]
    def __repr__(s):
        for _ in (): pass
        log.append("repr")
        if isinstance(s.rep, type): raise s.rep("bad")
        return s.rep
class Sub(str): pass
def t(f):
    del log[:]
    try: r = f()
    except Exception as e: return (type(e).__name__, str(e), log[:])
    return (type(r).__name__, repr(r), r.exceptions, log[:])

def cases():
    v, w = ValueError(1), TypeError(2)
    return [t(lambda: ExceptionGroup("m", Seq([v, w]))), t(lambda: BaseExceptionGroup("m", Seq([v]))),
            t(lambda: ExceptionGroup("m", Seq([KeyboardInterrupt()]))), t(lambda: ExceptionGroup("m", Seq([]))),
            t(lambda: ExceptionGroup("m", Seq([1]))), t(lambda: ExceptionGroup("m", Seq([v], None))),
            t(lambda: ExceptionGroup("m", Seq([v], LookupError))), t(lambda: ExceptionGroup("m", Seq([v], Sub("sub")))),
            t(lambda: ExceptionGroup(1, Seq([v])))], v, w
got, v, w = cases()
assert_eq(got, [
    ("ExceptionGroup", "ExceptionGroup('m', Seq(...))", (v, w), ["repr", ("get", 0), ("get", 1), ("get", 2)]),
    ("ExceptionGroup", "ExceptionGroup('m', Seq(...))", (v,), ["repr", ("get", 0), ("get", 1)]),
    ("TypeError", "Cannot nest BaseExceptions in an ExceptionGroup", ["repr", ("get", 0), ("get", 1)]),
    ("ValueError", "second argument (exceptions) must be a non-empty sequence", ["repr", ("get", 0)]),
    ("ValueError", "Item 0 of second argument (exceptions) is not an exception", ["repr", ("get", 0), ("get", 1)]),
    ("TypeError", "Seq.__repr__() must return a str, not NoneType", ["repr"]),
    ("LookupError", "bad", ["repr"]),
    ("ExceptionGroup", "ExceptionGroup('m', sub)", (v,), ["repr", ("get", 0), ("get", 1)]),
    ("TypeError", "BaseExceptionGroup.__new__() argument 1 must be str, not int", [])])

s = Seq([v], "kept"); g = ExceptionGroup("m", s); s.items.clear(); s.rep = "changed"; g.args = ()
assert_eq((repr(g), g.exceptions), ("ExceptionGroup('m', kept)", (v,)))

class EG(ExceptionGroup):
    def __init__(s, *a):
        for _ in (): pass
        log.append(("init", a[0]))
        super().__init__(*a)
class EB(BaseExceptionGroup):
    def __new__(cls, m, e):
        for _ in (): pass
        log.append("new")
        return super().__new__(cls, m, e)
    def __init__(s, m, e):
        for _ in (): pass
        log.append("init")
assert_eq(t(lambda: EG("m", Seq([v]))), ("EG", "EG('m', Seq(...))", (v,), ["repr", ("get", 0), ("get", 1), ("init", "m")]))
assert_eq(t(lambda: EB("m", Seq([v]))), ("EB", "EB('m', Seq(...))", (v,), ["new", "repr", ("get", 0), ("get", 1), "init"]))
assert_eq(t(lambda: EB("m", Seq([], None))), ("TypeError", "Seq.__repr__() must return a str, not NoneType", ["new", "repr"]))
assert_eq(t(lambda: BaseExceptionGroup.__new__(BaseExceptionGroup, "m", Seq([v]))),
          ("ExceptionGroup", "ExceptionGroup('m', Seq(...))", (v,), ["repr", ("get", 0), ("get", 1)]))

try:
    raise ExceptionGroup("m", Seq([ValueError(7), TypeError(8)]))
except* ValueError as e: parts = [repr(e)]
except* TypeError as e: parts.append(repr(e))
assert_eq(parts, ["ExceptionGroup('m', [ValueError(7)])", "ExceptionGroup('m', [TypeError(8)])"])
