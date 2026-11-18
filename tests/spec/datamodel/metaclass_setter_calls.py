# spec: PLS-315 7.3.7, 7.3.8, 7.3.9
# description: a store to or deletion of a class's attribute, by
# assignment, del, setattr(), delattr() or a for target, calls its
# metaclass's Python __setattr__ or __delattr__, which may loop, or a data
# descriptor or property the metaclass defines: its __set__, __delete__ or
# setter, with the class; the hook's result is ignored and its exception
# propagates. Inside functions as at module level.
from harness import *

log = []
def spin():
    for _ in range(2): pass
class Meta(type):
    def __setattr__(cls, name, value):
        spin(); log.append(("set", cls.__name__, name, value))
        super().__setattr__(name, value)
    def __delattr__(cls, name):
        spin(); log.append(("del", cls.__name__, name))
        super().__delattr__(name)
class C(metaclass=Meta): pass
class Frozen(type):
    def __setattr__(cls, name, value): spin(); raise AttributeError("frozen " + name)
class F(metaclass=Frozen): pass
class Desc:
    def __set__(self, obj, value): spin(); log.append(("dset", obj.__name__, value))
    def __delete__(self, obj): spin(); log.append(("ddel", obj.__name__))
    def __get__(self, obj, owner=None): return "got"
class DM(type):
    d = Desc()
    @property
    def p(cls): return cls._p
    @p.setter
    def p(cls, v): spin(); log.append(("pset", v)); type.__setattr__(cls, "_p", v)
class D(metaclass=DM): pass
class R(type):
    def __setattr__(cls, name, value): spin(); return 42
class E(metaclass=R): pass
def err(f):
    try:
        return f()
    except Exception as e:
        return (type(e).__name__, str(e))
def run():
    del log[:]
    out = []
    C.x = 1
    setattr(C, "y", 2)
    out.append((C.x, C.y))
    del C.x
    delattr(C, "y")
    out.append(err(lambda: C.x))
    out.append(err(lambda: setattr(F, "a", 1)))
    def assign(): F.b = 2
    out.append(err(assign))
    D.d = 5
    del D.d
    setattr(D, "d", 6)
    D.p = 7
    out.append((D.d, D.p))
    out.append(setattr(E, "z", 1))
    E.w = 2
    out.append(err(lambda: E.w))
    C.x, C.y = 3, 4
    out.append((C.x, C.y))
    for C.i in range(2): pass
    out.append(C.i)
    out.append(err(lambda: delattr(C, "nope")))
    return out, list(log)

expected = ([(1, 2), ('AttributeError', "type object 'C' has no attribute 'x'"), ('AttributeError', 'frozen a'), ('AttributeError', 'frozen b'), ('got', 7), None, ('AttributeError', "type object 'E' has no attribute 'w'"), (3, 4), 1, ('AttributeError', "type object 'C' has no attribute 'nope'")],
            [('set', 'C', 'x', 1), ('set', 'C', 'y', 2), ('del', 'C', 'x'), ('del', 'C', 'y'), ('dset', 'D', 5), ('ddel', 'D'), ('dset', 'D', 6), ('pset', 7), ('set', 'C', 'x', 3), ('set', 'C', 'y', 4), ('set', 'C', 'i', 0), ('set', 'C', 'i', 1), ('del', 'C', 'nope')])

def main():
    return run()

assert_eq(main(), expected)
assert_eq(run(), expected)
