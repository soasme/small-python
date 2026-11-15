# spec: PLS-315 15.4.1, 15.4.3, 9.3.5
# description: an except or except* clause's as name is stored when it
# matches and, when its block ends normally, by continue or break, or by
# an exception, stored None and then deleted, by its namespace's Python
# __setitem__ and __delitem__, each of which may loop: a block that
# deleted the name or rebound it still ends so, and an exception from
# the unbinding replaces the one the block raised, its context the
# exception the clause handles; after a block that ended otherwise, an
# except clause's unbinding has the exception handled before it. A
# function's handler leaves its local unbound. In class bodies and
# modules executed with a mapping.
from harness import *

log = []

class NS(dict):
    def __setitem__(self, k, v):
        for _ in (): pass
        if not k.startswith("__"): log.append(("set", k, v if v is None else type(v).__name__))
        super().__setitem__(k, v)
    def __delitem__(self, k):
        for _ in (): pass
        log.append(("del", k))
        super().__delitem__(k)

def run(source):
    log.clear()
    exec(source, {}, NS())
    return log[:]

caught = [("set", "e", "ZeroDivisionError"), ("set", "e", None), ("del", "e")]
assert_eq(run("try: 1/0\nexcept ZeroDivisionError as e: pass\n"), caught)
assert_eq(run("try: 1/0\nexcept ZeroDivisionError as e: del e\n"),
          [("set", "e", "ZeroDivisionError"), ("del", "e"), ("set", "e", None), ("del", "e")])
assert_eq(run("try: 1/0\nexcept ZeroDivisionError as e:\n    e = 5\n"),
          [("set", "e", "ZeroDivisionError"), ("set", "e", "int"), ("set", "e", None), ("del", "e")])
assert_eq(run("for i in range(2):\n    try: 1/0\n    except ZeroDivisionError as e: continue\n"),
          [("set", "i", "int")] + caught + [("set", "i", "int")] + caught)
assert_eq(run("while True:\n    try: 1/0\n    except ZeroDivisionError as e: break\n"), caught)
assert_eq(run("try: raise ExceptionGroup('g', [ValueError(1), KeyError(2)])\nexcept* ValueError as v: pass\nexcept* KeyError as k: pass\n"),
          [("set", "v", "ExceptionGroup"), ("set", "v", None), ("del", "v"), ("set", "k", "ExceptionGroup"), ("set", "k", None), ("del", "k")])

def raising(source):
    try: run(source)
    except Exception as e: return log[:], type(e).__name__, type(e.__context__).__name__
assert_eq(raising("try: 1/0\nexcept ZeroDivisionError as e: raise KeyError\n"), (caught, "KeyError", "ZeroDivisionError"))
assert_eq(raising("try: raise ExceptionGroup('g', [ValueError(1)])\nexcept* ValueError as v: raise KeyError\n"),
          ([("set", "v", "ExceptionGroup"), ("set", "v", None), ("del", "v")], "KeyError", "ExceptionGroup"))
assert_eq(raising("for i in (1,):\n    try: 1/0\n    except ZeroDivisionError as e:\n        try: raise KeyError\n        finally: del e\n"),
          ([("set", "i", "int"), ("set", "e", "ZeroDivisionError"), ("del", "e"), ("set", "e", None), ("del", "e")], "KeyError",
           "ZeroDivisionError"))

class Gone(NS):
    def __delitem__(self, k):
        for _ in (): pass
        raise LookupError(k)
def gone(source):
    try: exec(source, {}, Gone())
    except NameError as e: return str(e), type(e.__context__).__name__
assert_eq([gone(source) for source in (
    "try: 1/0\nexcept ZeroDivisionError as e: raise KeyError\n",
    "try: 1/0\nexcept ZeroDivisionError as e: pass\n",
    "for i in (1,):\n    try: 1/0\n    except ZeroDivisionError as e: break\n",
    "try: raise ValueError\nexcept ValueError:\n    try: 1/0\n    except ZeroDivisionError as e: pass\n",
    "try: raise ExceptionGroup('g', [ValueError(1)])\nexcept* ValueError as v: pass\n",
    "try: raise ExceptionGroup('g', [ValueError(1)])\nexcept* ValueError as v: raise KeyError\n")],
    [("name 'e' is not defined", "ZeroDivisionError"), ("name 'e' is not defined", "NoneType"), ("name 'e' is not defined", "NoneType"),
     ("name 'e' is not defined", "ValueError"), ("name 'v' is not defined", "ExceptionGroup"),
     ("name 'v' is not defined", "ExceptionGroup")])

class Meta(type):
    @classmethod
    def __prepare__(m, n, b): return NS()

log.clear()
class K(metaclass=Meta):
    try: 1/0
    except ZeroDivisionError as e: pass
assert_eq(log, caught)
assert_true("e" not in K.__dict__)
log.clear()
try:
    class R(metaclass=Meta):
        try: 1/0
        except ZeroDivisionError as e: raise KeyError
except KeyError: pass
assert_eq(log, caught)

def inside():
    try: 1/0
    except ZeroDivisionError as e: pass
    try: e
    except NameError as n: return str(n)

assert_eq(inside(), "cannot access local variable 'e' where it is not associated with a value")
