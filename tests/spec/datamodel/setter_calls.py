# spec: PLS-315 7.3.7, 7.3.8, 20.5
# description: An attribute store calls the instance class's Python
# __setattr__ with the name and value; else a property's setter with the
# instance and value, or a data descriptor's __set__ with the descriptor,
# instance and value, before any instance entry. A deletion calls
# __delattr__ with the name, a property's deleter, or __delete__ with the
# descriptor and instance. Their results are ignored and their exceptions
# propagate; a property without a setter or deleter raises AttributeError.
# Simple, chained, target-list, loop and augmented stores each call once per
# target, the value evaluated once. Methods that loop run in function
# statements as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Hooked:
    def __setattr__(self, name, value):
        spin()
        log.append(("setattr", name, value))
        if value == "bad":
            raise KeyError(name)
        object.__setattr__(self, name, value)
        return "ignored"

class Deleting:
    def __delattr__(self, name):
        spin()
        log.append(("delattr", name))
        if name == "bad":
            raise KeyError(name)
        return "ignored"

class Arity:
    def __setattr__(self, name):
        spin()

class Prop:
    def __init__(self): self.__dict__["_v"] = 0
    @property
    def p(self): return self._v
    @p.setter
    def p(self, value):
        spin()
        log.append(("fset", value))
        if value == "bad":
            raise ValueError("fset")
        self._v = value
    @p.deleter
    def p(self):
        spin()
        log.append(("fdel",))
        self.__dict__["_v"] = -1
    @property
    def ro(self): return 1

class Desc:
    def __get__(self, obj, owner): return obj.__dict__.get("_d", "unset")
    def __set__(self, obj, value):
        spin()
        log.append(("set", type(self).__name__, type(obj).__name__, value))
        obj.__dict__["_d"] = value
        return "ignored"
    def __delete__(self, obj):
        spin()
        log.append(("delete", type(obj).__name__))
        obj.__dict__.pop("_d")

class Owner:
    d = Desc()

def value(v):
    log.append(("value", v))
    return v

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def stores():
    del log[:]
    h, p, o = Hooked(), Prop(), Owner()
    h.x = value(1)
    x = h.y = p.p = value(2)
    h.a, p.p = 3, 4
    for o.d in range(2): pass
    o.__dict__["d"] = "shadow"
    o.d = 5
    p.p += 1
    def bad_hook(): h.z = "bad"
    def bad_arity():
        a = Arity()
        a.x = 1
    def bad_fset(): p.p = "bad"
    def readonly(): p.ro = 1
    out = [h.x, h.y, h.a, x, p.p, o.d, o.__dict__["d"],
           error(bad_hook), error(bad_arity), error(bad_fset), error(readonly)]
    d = Deleting()
    del d.k, p.p
    del o.d
    def bad_del(): del d.bad
    def no_deleter(): del p.ro
    def twice(): del o.d
    out += [p.p, o.d, error(bad_del), error(no_deleter), error(twice)[0]]
    out.append(list(log))
    return out

expected = [1, 2, 3, 2, 5, 5, "shadow",
            ("KeyError", "'z'"),
            ("TypeError", "Arity.__setattr__() takes 2 positional arguments but 3 were given"),
            ("ValueError", "fset"),
            ("AttributeError", "property 'ro' of 'Prop' object has no setter"),
            -1, "unset", ("KeyError", "'bad'"), ("AttributeError", "property 'ro' of 'Prop' object has no deleter"), "KeyError",
            [("value", 1), ("setattr", "x", 1), ("value", 2), ("setattr", "y", 2), ("fset", 2),
             ("setattr", "a", 3), ("fset", 4),
             ("set", "Desc", "Owner", 0), ("set", "Desc", "Owner", 1), ("set", "Desc", "Owner", 5),
             ("fset", 5), ("setattr", "z", "bad"), ("fset", "bad"),
             ("delattr", "k"), ("fdel",), ("delete", "Owner"), ("delattr", "bad"), ("delete", "Owner")]]

assert_eq(stores(), expected)
assert_eq(stores(), expected)
del log[:]
top = Hooked()
top.t = 7
assert_eq([top.t, log], [7, [("setattr", "t", 7)]])
