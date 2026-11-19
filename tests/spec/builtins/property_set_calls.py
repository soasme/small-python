# spec: PLS-315 20.5.1
# description: property's __set__(instance, value) and __delete__(instance)
# called as methods, from the property or its class, from a subclass's
# instance, or bound, call fset or fdel with the instance (and the value)
# and return None whatever the function returned; an exception the function
# raises propagates, and a missing function raises AttributeError naming the
# setter or deleter. Inside functions as at module level.
from harness import *

log = []

class C:
    def get(self):
        return "got"
    def put(self, value):
        for _ in range(2): pass
        log.append(("set", value))
        if value == "bad": raise LookupError(value)
        return "ignored"
    def drop(self):
        for _ in range(2): pass
        log.append("delete")
        return "ignored"
    x = property(get, put, drop)
    y = property(get)

class P(property):
    pass

class D:
    def put(self, value):
        log.append(("sub", value))
    z = P(None, put, lambda self: log.append("subdel"))

def run():
    del log[:]
    c = C()
    results = [C.x.__set__(c, 1), property.__set__(C.x, c, 2), C.x.__delete__(c), property.__delete__(C.x, c)]
    bound = C.x.__set__
    results.append(bound(c, 3))
    e = assert_raises(LookupError, C.x.__set__, c, "bad")
    results.append(e.args)
    e = assert_raises(AttributeError, C.y.__set__, c, 4)
    results.append(str(e))
    e = assert_raises(AttributeError, C.y.__delete__, c)
    results.append(str(e))
    d = D()
    results += [D.z.__set__(d, 5), D.z.__delete__(d)]
    return results, log[:]

expected = ([None, None, None, None, None, ("bad",), "property 'y' of 'C' object has no setter",
             "property 'y' of 'C' object has no deleter", None, None],
            [("set", 1), ("set", 2), "delete", "delete", ("set", 3), ("set", "bad"), ("sub", 5), "subdel"])

assert_eq(run(), expected)

def main():
    return run()

assert_eq(main(), expected)
