# spec: PLS-315 16.4.1, 16.7
# description: A generic class's bases and keywords are evaluated in its
# type parameters' scope, before its generic base is added; its metaclass's
# __prepare__ gets them all, its body that calls and loops sees the type
# parameters and runs its statements in order, its methods reach __class__
# and super(), and an exception from the body propagates and makes no
# class, inside functions as at module level. A class of bases whose
# body only assigns has its type parameters too.
from harness import *

log = []

def note(x):
    for _ in range(2): pass
    log.append(x)
    return x

class Meta(type):
    @classmethod
    def __prepare__(mcls, name, bases, **kw):
        log.append(("prepare", name, len(bases), sorted(kw)))
        return {}
    def __new__(mcls, name, bases, ns, **kw):
        return super().__new__(mcls, name, bases, ns)

class Base:
    def size(self): return note(2)

def results():
    del log[:]
    class Box[T, *Ts](note(Base), metaclass=Meta, flag=note(1)):
        kinds = [note(T.__name__), Ts.__name__]
        for i in range(2):
            note(i)
        def size(self): return super().size() + 1
        def owner(self): return __class__
    out = [list(log), Box.__type_params__, Box.__orig_bases__[0] is Base, len(Box.__orig_bases__), Box.kinds, Box.i,
           Box().size(), Box().owner() is Box, type(Box) is Meta, Box.__qualname__]
    class Plain[K](Base): k = K
    out.append(Plain.__type_params__ == (Plain.k,) and Plain().size() == 2)
    try:
        class Broken[T]:
            note(T)
            note(1 // 0)
        out.append("made")
    except ZeroDivisionError:
        out.append("Broken" in locals())
    return out

expected = [[Base, 1, ("prepare", "Box", 2, ["flag"]), "T", 0, 1], "params", True, 2, ["T", "Ts"], 1,
            3, True, True, "results.<locals>.Box", True, False]

def main():
    return results()

def check(out):
    assert_eq([str(p) for p in out[1]], ["T", "Ts"])
    out[1] = "params"
    assert_eq(out, expected)

check(main())
check(results())
