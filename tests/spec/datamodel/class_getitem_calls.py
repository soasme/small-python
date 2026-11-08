# spec: PLS-315 7.8.1, 16.4
# description: Subscripting a class calls its metaclass's __getitem__, else
# its __class_getitem__, an implicit classmethod that subclasses inherit,
# either of which may loop, inside functions as at module level; their
# exceptions propagate. A metaclass's __getattribute__ or class attribute
# can supply __class_getitem__, a plain function or staticmethod stored
# later is called with the key alone, and None or a missing one raises
# TypeError, as does a method that cannot take the key.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Generic:
    def __class_getitem__(cls, key):
        spin()
        log.append((cls.__name__, key))
        if key == "bad":
            raise KeyError(key)
        return (cls.__name__, key)

class Derived(Generic): pass

class Meta(type):
    def __getitem__(cls, key):
        spin()
        return ("meta", cls.__name__, key)

class Indexed(metaclass=Meta):
    def __class_getitem__(cls, key): return "never"

class Kind(type): pass

class Kinded(metaclass=Kind):
    def __class_getitem__(cls, key):
        spin()
        return ("kinded", key)

class Intercepting(type):
    def __getattribute__(cls, name):
        if name == "__class_getitem__": return lambda key: ("intercepted", key)
        return type.__getattribute__(cls, name)

class Intercepted(metaclass=Intercepting):
    def __class_getitem__(cls, key): return "own"

class Offering(type):
    __class_getitem__ = classmethod(lambda cls, key: ("offered", key))

class Offered(metaclass=Offering): pass

class Late: pass
Late.__class_getitem__ = lambda key: ("late", key)

class Static:
    __class_getitem__ = staticmethod(lambda key: ("static", key))

class Disabled:
    __class_getitem__ = None

class Plain: pass

class Arity:
    def __class_getitem__(cls): spin()

def error(f):
    try:
        return f()
    except Exception as e:
        return type(e).__name__, str(e)

def results():
    del log[:]
    out = [Generic[int], Derived[1, 2], error(lambda: Generic["bad"]), Indexed[3], Kinded[4],
           Intercepted[5], Offered[6], Late[7], Static[8], error(lambda: Disabled[9]), error(lambda: Plain[10]), error(lambda: Arity[11])]
    out.append(list(log))
    return out

expected = [("Generic", int), ("Derived", (1, 2)), ("KeyError", "'bad'"), ("meta", "Indexed", 3),
            ("kinded", 4), ("intercepted", 5), ("offered", 6), ("late", 7), ("static", 8),
            ("TypeError", "type 'Disabled' is not subscriptable"),
            ("TypeError", "type 'Plain' is not subscriptable"),
            ("TypeError", "Arity.__class_getitem__() takes 1 positional argument but 2 were given"),
            [("Generic", int), ("Derived", (1, 2)), ("Generic", "bad")]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
