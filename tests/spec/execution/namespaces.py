# spec: PLS-315 9.1, 9.3, 28.6
# description: Globals, builtins, locals mappings, fast locals, and cells.
from harness import *

# The globals of a module are its __dict__, a dict.
assert_type(globals(), dict)
assert_is(globals(), host.module_cache()[__name__].__dict__)
# The builtins are reached from the globals.
ns = run("r = len('ab')\n")
assert_eq(ns["r"], 2)
assert_true("__builtins__" in ns)
ns = run("r = len\n", {"__builtins__": {"len": "mine"}})
assert_eq(ns["r"], "mine")

# The locals of exec and of a class body may be any mapping.
class Recorder(dict):
    def __init__(self):
        self.log = []
    def __getitem__(self, key):
        self.log.append(("get", key))
        return dict.__getitem__(self, key)
    def __setitem__(self, key, value):
        self.log.append(("set", key))
        dict.__setitem__(self, key, value)
locals_map = Recorder()
exec("x = 1\ny = x\n", {}, locals_map)
assert_eq(locals_map.log, [("set", "x"), ("get", "x"), ("set", "y")])
class Mapping:
    def __init__(self): self.data = {}
    def __getitem__(self, key): return self.data[key]
    def __setitem__(self, key, value): self.data[key] = value
m = Mapping()
exec("a = 2\nb = a * 3\n", {}, m)
assert_eq(m.data, {"a": 2, "b": 6})

# Fast locals: one slot per local name, unbound until assigned.
def f():
    try:
        v
    except UnboundLocalError as e:
        message = str(e)
    v = 1
    return message
assert_eq(f(), "cannot access local variable 'v' where it is not associated with a value")
assert_true("v" in f.__code__.co_varnames)

# Cells: shared between the scope that creates them and nested functions.
def outer():
    c = 0
    def get(): return c
    def put(v):
        nonlocal c
        c = v
    return get, put
get, put = outer()
put(5)
assert_eq(get(), 5)
assert_eq(get.__closure__[0].cell_contents, 5)
assert_is(get.__closure__[0], put.__closure__[0])
assert_eq(outer.__code__.co_cellvars, ("c",))
assert_eq(get.__code__.co_freevars, ("c",))
# A cell is created when the frame starts, empty until bound.
def early():
    def read(): return late
    try:
        read()
    except NameError as e:
        message = str(e)
    late = 1
    return message
assert_eq(early(), "cannot access free variable 'late' where it is not associated with a value in enclosing scope")
