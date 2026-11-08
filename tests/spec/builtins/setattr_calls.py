# spec: PLS-315 19.3.11, 7.3.7, 7.3.8
# description: setattr(object, name, value) stores the attribute as an
# assignment does: through the class's __setattr__, a property's setter
# or a data descriptor's __set__, each of which may loop, inside functions
# as at module level; it returns None, the setter's result unused, and a
# setter's exception propagates. A property without a setter raises
# AttributeError, and a str subclass names the attribute.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Descriptor:
    def __get__(self, obj, owner): return obj.__dict__.get("_d")
    def __set__(self, obj, value):
        spin()
        log.append(("set", value))
        obj.__dict__["_d"] = value * 2
        return "ignored"

class Thing:
    d = Descriptor()
    @property
    def p(self): return self._p
    @p.setter
    def p(self, value):
        spin()
        log.append(("p", value))
        if value == "bad":
            raise ValueError("bad p")
        self._p = value
    @property
    def fixed(self): return 1

class Hooked:
    def __setattr__(self, name, value):
        spin()
        log.append(("setattr", name, value))
        object.__setattr__(self, name, value + 1)

class Name(str): pass

def error(f):
    try:
        f()
    except Exception as e:
        return type(e).__name__, str(e)

def stores():
    del log[:]
    t, h = Thing(), Hooked()
    out = [setattr(t, "p", 1), t.p, setattr(t, "d", 5), t.d, setattr(t, "plain", 7), t.plain,
           setattr(h, "x", 10), h.x, setattr(t, Name("p"), 2), t.p]
    out.append(error(lambda: setattr(t, "p", "bad")))
    out.append(error(lambda: setattr(t, "fixed", 3)))
    results = []
    results.append(setattr(h, "y", 0))
    out += [results, h.y, list(log)]
    return out

expected = [None, 1, None, 10, None, 7, None, 11, None, 2,
            ("ValueError", "bad p"),
            ("AttributeError", "property 'fixed' of 'Thing' object has no setter"),
            [None], 1,
            [("p", 1), ("set", 5), ("setattr", "x", 10), ("p", 2), ("p", "bad"), ("setattr", "y", 0)]]

def main():
    return stores()

assert_eq(main(), expected)
assert_eq(stores(), expected)
