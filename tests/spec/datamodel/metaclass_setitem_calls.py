# spec: PLS-315 7.8.2
# description: Assigning to and deleting a subscript of a class calls its
# metaclass's Python __setitem__ and __delitem__, which a subclass
# inherits and which may loop or raise, inside functions as at module
# level, in chained and tuple assignments; a class whose metaclass is type
# supports neither.
from harness import *

log = []
class Meta(type):
    def __setitem__(cls, key, value):
        for _ in (): pass
        log.append(("set", cls.__name__, key, value))
        if key == "bad": raise KeyError(key)
    def __delitem__(cls, key):
        for _ in (): pass
        log.append(("del", cls.__name__, key))
        if key == "bad": raise LookupError(key)
class K(metaclass=Meta): pass
class Sub(K): pass
def run(f):
    del log[:]
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r, log[:]
def store(t, k, v):
    t[k] = v
def delete(t, k):
    del t[k]
def chained():
    K["a"] = Sub["b"] = 1
    K["x"], Sub["y"] = 2, 3
    K["n"] += 0 if False else 0
class Plain: pass

def results():
    out = [run(lambda: store(K, "k", 1)), run(lambda: store(Sub, "s", 2)), run(lambda: store(K, "bad", 3)),
           run(lambda: delete(K, "k")), run(lambda: delete(Sub, "bad")), run(chained),
           run(lambda: store(Plain, "p", 1)), run(lambda: delete(Plain, "p"))]
    return out

expected = [(None, [("set", "K", "k", 1)]), (None, [("set", "Sub", "s", 2)]), (("KeyError", "'bad'"), [("set", "K", "bad", 3)]),
            (None, [("del", "K", "k")]), (("LookupError", "bad"), [("del", "Sub", "bad")]),
            (("TypeError", "type 'K' is not subscriptable"), [("set", "K", "a", 1), ("set", "Sub", "b", 1), ("set", "K", "x", 2), ("set", "Sub", "y", 3)]),
            (("TypeError", "'type' object does not support item assignment"), []),
            (("TypeError", "'type' object does not support item deletion"), [])]
assert_eq(results(), expected)
del log[:]
K["top"] = 5
del K["top"]
assert_eq(log, [("set", "K", "top", 5), ("del", "K", "top")])
