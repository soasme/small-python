# spec: PLS-315 7.3.4, 7.3.7, 7.3.8, 7.3.9
# description: getattr, hasattr, setattr and delattr given a str subclass's
# instance pass that object itself as the name: to __getattribute__,
# __getattr__, __setattr__ and __delattr__, as an AttributeError's name,
# and as the key a plain instance's namespace binds, also when a map calls
# getattr or hasattr. Inside functions as at module level.
from harness import *

class N(str): pass

class Hooked:
    def __getattr__(self, name):
        for _ in (): pass
        return name
    def __setattr__(self, name, value):
        for _ in (): pass
        log.append(name)
    def __delattr__(self, name):
        for _ in (): pass
        log.append(name)

class Intercepted:
    def __getattribute__(self, name):
        for _ in (): pass
        return name

class Missing:
    def __getattr__(self, name):
        for _ in (): pass
        raise AttributeError(name)

class Plain: pass

log = []

def names(n):
    del log[:]
    h = Hooked()
    setattr(h, n, 1)
    delattr(h, n)
    p = Plain()
    setattr(p, n, 2)
    error = assert_raises(AttributeError, getattr, Plain(), n)
    ga = assert_raises(AttributeError, object.__getattribute__, Plain(), n)
    return [getattr(h, n) is n, hasattr(h, n), getattr(Intercepted(), n) is n,
            getattr(Missing(), n, 3), log[0] is n, log[1] is n,
            list(p.__dict__)[0] is n, type(list(p.__dict__)[0]) is N, p.zz,
            error.name is n, ga.name is n, getattr(p, n) == 2,
            list(map(getattr, [p, Plain()], [n, n], [0, 4])), list(map(hasattr, [p, Plain()], [n, n]))]

expected = [True, True, True, 3, True, True, True, True, 2, True, True, True, [2, 4], [True, False]]

def main():
    return names(N("zz"))

assert_eq(main(), expected)
assert_eq(names(N("zz")), expected)
