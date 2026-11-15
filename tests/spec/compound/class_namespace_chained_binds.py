# spec: PLS-315 16.4.2, 14.2, 14.4, 9.3.5
# description: a class body whose namespace's class has a Python
# __setitem__ and __delitem__, each of which may loop, stores a chained
# assignment's names left to right by __setitem__, after the value is
# made, and deletes a del's target list, nested lists included, left to
# right by __delitem__, an error of which becomes a NameError for its
# name and stops the deletes after it. Inside functions as at module
# level.
from harness import *

log = []

class NS(dict):
    def __setitem__(self, k, v):
        for _ in (): pass
        if not k.startswith("__"): log.append(("set", k))
        super().__setitem__(k, v)
    def __delitem__(self, k):
        for _ in (): pass
        log.append(("del", k))
        if k == "gone": raise LookupError(k)
        super().__delitem__(k)

class Meta(type):
    @classmethod
    def __prepare__(m, n, b): return NS()

def value():
    log.append("value")
    return 1

def run():
    class K(metaclass=Meta):
        a = b = c = value()
        del [a, (b, c)]
        x = y = 2
        try: del x, gone, y
        except NameError as e: log.append(str(e))
    return sorted(k for k in K.__dict__ if not k.startswith("__"))

assert_eq(run(), ["y"])
assert_eq(log[:13], ["value", ("set", "a"), ("set", "b"), ("set", "c"), ("del", "a"), ("del", "b"), ("del", "c"),
                     ("set", "x"), ("set", "y"), ("del", "x"), ("del", "gone"), ("set", "e"), "name 'gone' is not defined"])
log.clear()

class Top(metaclass=Meta):
    p = q = 3
    del p, q

assert_eq(log, [("set", "p"), ("set", "q"), ("del", "p"), ("del", "q")])
