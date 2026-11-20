# spec: PLS-315 10.4.2, 20.2.6, 19.3.11
# description: assigning a class's __bases__, by an assignment, a for
# target or setattr(), recomputes the MRO of the class and then of each
# of its subclasses, oldest first, calling a metaclass's Python mro(),
# which may loop, once per class; when one raises, every MRO already
# recomputed and the class's bases are restored and the exception
# propagates. Inside functions as at module level.
from harness import *

log = []
class M(type):
    def mro(cls):
        for _ in (): pass
        log.append(cls.__name__)
        if getattr(cls, "fail", False): raise LookupError("mro")
        return type.mro(cls)
class A: pass
class B: pass
class C(A, metaclass=M): pass
class D(C): pass
class E(D): pass

def names(cls): return [k.__name__ for k in cls.__mro__]

def assign(store):
    del log[:]
    store((B,))
    r = [names(C), names(E), list(log)]
    del log[:]
    D.fail = True
    try: store((A,))
    except LookupError: r.append(("LookupError", C.__bases__ == (B,), names(D), names(E), list(log)))
    del D.fail
    del log[:]
    store((A,))
    return r + [names(E), list(log)]

def by_assignment(bases): C.__bases__ = bases
def by_for(bases):
    for C.__bases__ in [bases]: pass
def by_setattr(bases): setattr(C, "__bases__", bases)

expected = [["C", "B", "object"], ["E", "D", "C", "B", "object"], ["C", "D", "E"],
            ("LookupError", True, ["D", "C", "B", "object"], ["E", "D", "C", "B", "object"], ["C", "D"]),
            ["E", "D", "C", "A", "object"], ["C", "D", "E"]]
for store in (by_assignment, by_for, by_setattr):
    assert_eq(assign(store), expected)

del log[:]
C.__bases__ = (B,)
assert_eq([names(E), log], [["E", "D", "C", "B", "object"], ["C", "D", "E"]])
C.__bases__ = (A,)
