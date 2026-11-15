# spec: PLS-315 15.3, 14.7, 9.3.5, 19.3.15
# description: a module body run by exec() with a locals mapping binds a
# for loop's name through the mapping's Python __setitem__ on each pass,
# also of a generator's items, deletes a name, and each name of del a, b,
# in order, through its Python __delitem__; an exception from __setitem__
# leaves the loop, one from __delitem__ is a NameError, with no context,
# that stops the del before its later names. A plain dict's loop binds as
# before.
from harness import *

log = []

class Namespace(dict):
    def __setitem__(self, key, value):
        for _ in (): pass
        log.append(("set", key, value))
        if value == "stop": raise KeyError(key)
        dict.__setitem__(self, key, value)
    def __delitem__(self, key):
        for _ in (): pass
        log.append(("del", key))
        if key == "x": raise LookupError(key)
        dict.__delitem__(self, key)

ns = Namespace()
exec("for i in (1, 2): j = i\na = b = 0\ndel a, b\nk = 1\ndel k\n", {}, ns)
assert_eq(log, [("set", "i", 1), ("set", "j", 1), ("set", "i", 2), ("set", "j", 2), ("set", "a", 0), ("set", "b", 0),
                ("del", "a"), ("del", "b"), ("set", "k", 1), ("del", "k")])
assert_eq(dict(ns), {"i": 2, "j": 2})
log.clear()

try: exec("for i in (1, 'stop', 3): pass\n", {}, Namespace())
except KeyError as e: log.append(("raised", e.args))
try: exec("x = y = 0\ndel x, y\n", {}, Namespace())
except NameError as e: log.append(("raised", str(e), type(e.__context__).__name__))
assert_eq(log, [("set", "i", 1), ("set", "i", "stop"), ("raised", ("i",)), ("set", "x", 0), ("set", "y", 0), ("del", "x"),
                ("raised", "name 'x' is not defined", "NoneType")])

log.clear()
exec("def g():\n    yield 1\n    yield from (2, 3)\nfor i in g(): pass\nfor j in enumerate(g()): pass\n", {}, Namespace())
assert_eq([entry[1:] for entry in log], [("g", log[0][2]), ("i", 1), ("i", 2), ("i", 3), ("j", (0, 1)), ("j", (1, 2)), ("j", (2, 3))])

plain = {}
exec("t = 0\nfor i in range(5): t += i\ndel i\n", {}, plain)
assert_eq(plain, {"t": 10})

def run():
    log.clear()
    exec("for i in 'ab': pass\ndel i\n", {}, Namespace())
    return log
assert_eq(run(), [("set", "i", "a"), ("set", "i", "b"), ("del", "i")])
