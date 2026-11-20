# spec: PLS-315 7.8.1
# description: Subscripting a class reads its __class_getitem__ as any
# attribute read does: a metaclass's Python __getattribute__, which may
# loop, raise AttributeError (the class then not subscriptable) or another
# exception, which propagates, and its __getattr__ fallback, called before
# the method, which may loop or raise too; a plain function, staticmethod or
# metaclass attribute is called with the key alone, each inside functions
# as at module level, in nested and chained subscripts.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Reading(type):
    def __getattribute__(cls, name):
        if name == "__class_getitem__":
            spin()
            log.append(("read", cls.__name__))
            mode = type.__getattribute__(cls, "mode")
            if mode == "missing": raise AttributeError(name)
            if mode == "error": raise KeyError(name)
            if mode == "none": return None
            if mode == "number": return 3
            return lambda key: (spin(), ("got", key))[1]
        return type.__getattribute__(cls, name)
    def __getattr__(cls, name):
        spin()
        log.append(("fallback", name))
        if type.__getattribute__(cls, "mode") == "missing": raise AttributeError(name)
        return lambda key: ("fallen", key)

def reading(mode):
    return Reading("R_" + mode, (), {"mode": mode})

class Fallback(type):
    def __getattr__(cls, name):
        spin()
        log.append(("getattr", name))
        if name == "__class_getitem__" and cls.__name__ == "Bad": raise ValueError("no")
        return staticmethod(lambda key: ("static", key)).__func__

Good = Fallback("Good", (), {})
Bad = Fallback("Bad", (), {})

class Late: pass
def late(key):
    spin()
    return [("late", key)]
Late.__class_getitem__ = late

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    out = [reading("ok")[1], error(lambda: reading("missing")[2]), error(lambda: reading("error")[3]),
           error(lambda: reading("none")[4]), error(lambda: reading("number")[5]),
           Good[6], error(lambda: Bad[7]), Late[8][0][1], (Late[9], Good[Late[10][0]])]
    out.append(list(log))
    return out

expected = [("got", 1), ("TypeError", "type 'R_missing' is not subscriptable"), ("KeyError", "'__class_getitem__'"),
            ("TypeError", "type 'R_none' is not subscriptable"), ("TypeError", "'int' object is not callable"),
            ("static", 6), ("ValueError", "no"), 8, ([("late", 9)], ("static", ("late", 10))),
            [("read", "R_ok"), ("read", "R_missing"), ("fallback", "__class_getitem__"), ("read", "R_error"),
             ("read", "R_none"), ("read", "R_number"), ("getattr", "__class_getitem__"), ("getattr", "__class_getitem__"),
             ("getattr", "__class_getitem__")]]

def main():
    return results()

assert_eq(results(), expected)
assert_eq(main(), expected)
