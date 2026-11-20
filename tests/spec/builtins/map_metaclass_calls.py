# spec: PLS-315 27.1.6, 19.3.1, 7.5.6
# description: map() of dir, str, repr, len or hash over classes whose
# metaclass defines the method in Python calls the metaclass's method
# for each class, in order, as calling the builtin on each does: dir()
# sorts what __dir__ gives, len() and hash() check their int, and an
# error in one propagates out of the map.
from harness import *

log = []
class Meta(type):
    def __dir__(cls):
        for _ in (): pass
        log.append(("dir", cls.__name__))
        return ["b", "a"]
    def __str__(cls):
        for _ in (): pass
        log.append(("str", cls.__name__))
        return "S" + cls.__name__
    def __repr__(cls):
        for _ in (): pass
        log.append(("repr", cls.__name__))
        return "R" + cls.__name__
    def __len__(cls):
        for _ in (): pass
        log.append(("len", cls.__name__))
        return len(cls.__name__)
    def __hash__(cls):
        for _ in (): pass
        log.append(("hash", cls.__name__))
        if cls.__name__ == "Bad": raise KeyError("bad")
        return 7

class A(metaclass=Meta): pass
class Bc(metaclass=Meta): pass
class Bad(metaclass=Meta): pass

def results():
    del log[:]
    out = [list(map(dir, [A, Bc])), list(map(str, [A])), list(map(repr, [Bc])), list(map(len, [A, Bc])), list(map(hash, [A]))]
    try: out.append(list(map(hash, [Bad, A])))
    except KeyError as e: out.append(("KeyError", str(e)))
    return out, list(log)

expected = ([[["a", "b"], ["a", "b"]], ["SA"], ["RBc"], [1, 2], [7], ("KeyError", "'bad'")],
            [("dir", "A"), ("dir", "Bc"), ("str", "A"), ("repr", "Bc"), ("len", "A"), ("len", "Bc"), ("hash", "A"), ("hash", "Bad")])

assert_eq(results(), expected)
assert_eq(results(), expected)
