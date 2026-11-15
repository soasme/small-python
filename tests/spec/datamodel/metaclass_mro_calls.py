# spec: PLS-315 16.4.3, 20.2.6
# description: A class made by a metaclass whose Python mro() overrides
# type.mro, in a class statement or a call of the metaclass, type.__new__
# or type(), has its MRO from mro(), which may loop and sees the class's
# namespace, called before the class's __set_name__ and __init_subclass__
# callbacks; its result is checked, and its exception, or a result that
# is no sequence of classes, fails the class's creation. Inside functions
# as at module level.
from harness import *

log = []

class Named:
    def __set_name__(self, owner, name): log.append(("set_name", name))

class Meta(type):
    def mro(cls):
        for _ in range(2): pass
        log.append(("mro", cls.__name__, "x" in cls.__dict__))
        if cls.__name__ == "Bad": raise LookupError("mro")
        if cls.__name__ == "Odd": return [cls, 1]
        if cls.__name__ == "Empty": return ()
        if cls.__name__ == "Flat": return (cls, object)
        return type.mro(cls)

class Base(metaclass=Meta):
    def __init_subclass__(cls): log.append(("init_subclass", cls.__name__))

def error(f, *args):
    try:
        f(*args)
    except Exception as e:
        return type(e).__name__, str(e)

def classes():
    del log[:]
    class Stated(Base):
        x = Named()
    made = Meta("Called", (Base,), {"x": 1})
    newed = type.__new__(Meta, "Newed", (Base,), {})
    class Flat(Base): pass
    out = [[k.__name__ for k in c.__mro__] for c in (Stated, made, newed, Flat)]
    out += [error(Meta, "Bad", (), {}), error(Meta, "Odd", (), {}), error(Meta, "Empty", (), {})]
    return out + [list(log)]

expected = [['Stated', 'Base', 'object'], ['Called', 'Base', 'object'], ['Newed', 'Base', 'object'], ['Flat', 'object'],
            ('LookupError', 'mro'), ('TypeError', "Odd.mro() returned a non-class ('int')"),
            ('TypeError', 'type MRO must not be empty'),
            [('mro', 'Stated', True), ('set_name', 'x'), ('init_subclass', 'Stated'), ('mro', 'Called', True),
             ('init_subclass', 'Called'), ('mro', 'Newed', False), ('init_subclass', 'Newed'), ('mro', 'Flat', False),
             ('mro', 'Bad', False), ('mro', 'Odd', False), ('mro', 'Empty', False)]]

def main():
    return classes()

assert_eq(main(), expected)
assert_eq(classes(), expected)
