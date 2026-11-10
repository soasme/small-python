# spec: PLS-315 14.2.2, 14.7, 16.4.2
# description: A class body whose namespace __prepare__ made a mapping with
# a Python __setitem__ binds each name it assigns, and its loops' targets,
# through that method, in order, with the name as key; and storing to or
# deleting an item of a dict subclass calls its Python __setitem__ or
# __delitem__. What they raise propagates from the statement, inside
# functions as at module level.
from harness import *

log = []

def spin():
    for _ in range(2): pass

class Recording(dict):
    def __setitem__(self, key, value):
        spin()
        if key == "bad": raise KeyError(key)
        if not key.startswith("__"): log.append(("set", key, value))
        super().__setitem__(key, value)
    def __delitem__(self, key):
        spin()
        log.append(("del", key))
        super().__delitem__(key)

class Meta(type):
    @classmethod
    def __prepare__(mcs, name, bases):
        return Recording()

def build():
    class Body(metaclass=Meta):
        a = 1
        b = c = len("ab")
        for i in range(2):
            spin()
        a += 10
    return Body

def failing():
    try:
        class Failing(metaclass=Meta):
            spin()
            bad = 1
    except KeyError as e:
        return str(e)

def items():
    d = Recording()
    d["x"] = 1
    d["y"] = 2
    d["x"] += 5
    del d["y"]
    try:
        d["bad"] = 3
    except KeyError:
        pass
    return dict(d)

def results():
    del log[:]
    body = build()
    out = [(body.a, body.b, body.c, body.i), list(log)]
    del log[:]
    out += [failing(), items(), list(log)]
    return out

expected = [(11, 2, 2, 1), [("set", "a", 1), ("set", "b", 2), ("set", "c", 2), ("set", "i", 0), ("set", "i", 1),
                            ("set", "a", 11)],
            "'bad'", {"x": 6}, [("set", "x", 1), ("set", "y", 2), ("set", "x", 6), ("del", "y")]]

def main():
    return results()

assert_eq(main(), expected)
assert_eq(results(), expected)
