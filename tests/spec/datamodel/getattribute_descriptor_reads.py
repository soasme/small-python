# spec: PLS-315 7.3.4, 19.3.21, 16.4.2
# description: a __getattribute__ that is a descriptor is bound by its
# Python __get__ before each call: an attribute read, isinstance()'s
# __class__ read and a class statement's read of a base's
# __mro_entries__ call it so; an AttributeError then falls back to
# __getattr__.
from harness import *
log = []
class Getter:
    def __get__(self, obj, owner):
        for _ in (): pass
        log.append(("get", type(obj).__name__))
        def look(name):
            log.append(name)
            if name == "__class__": return int
            if name == "__mro_entries__": return lambda bases: (object,)
            if name == "x": return "got x"
            raise AttributeError(name)
        return look
class Hooked:
    __getattribute__ = Getter()
class Falls:
    __getattribute__ = Getter()
    def __getattr__(self, name): return "fallback " + name
def run():
    h = Hooked()
    r = [h.x, isinstance(h, int), isinstance(h, str), Falls().z]
    class K(h): pass
    r.append(K.__mro__[1].__name__)
    return r, log
get = ("get", "Hooked")
assert_eq(run(), (["got x", True, False, "fallback z", "object"],
                  [get, "x", get, "__class__", get, "__class__", ("get", "Falls"), "z", get, "__mro_entries__"]))
