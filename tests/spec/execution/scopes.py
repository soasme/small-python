# spec: reference/executionmodel.html#naming-and-binding
# description: Local/global/nonlocal binding, class scope rules, free variables, UnboundLocalError.
from harness import *

x = "global"
def read(): return x
assert_eq(read(), "global")
def shadow():
    try:
        return x
    finally:
        pass
    x = 1
assert_raises(UnboundLocalError, shadow)
e = assert_raises(UnboundLocalError, shadow)
assert_true("x" in str(e))

def make():
    count = 0
    def inc():
        nonlocal count
        count += 1
        return count
    return inc
inc = make()
inc(); assert_eq(inc(), 2)
assert_eq(inc.__code__.co_freevars, ("count",))

def setter():
    global made
    made = 5
setter()
assert_eq(made, 5)

# Class scope does not extend to nested functions or comprehensions' bodies.
class C:
    y = 1
    def m(self):
        try:
            return y
        except NameError:
            return "no"
assert_eq(C().m(), "no")
assert_raises(NameError, run, "class D:\n    y = 1\n    l = [y for _ in range(2)]\n")
ns = run("class D:\n    y = [1, 2]\n    l = [v for v in y]\n")
assert_eq(ns["D"].l, [1, 2])

# A class body sees free variables of enclosing functions and its own locals first.
def f():
    v = "func"
    class K:
        v = "class"
        w = v
        def g(self): return v
    return K
K = f()
assert_eq((K.w, K().g()), ("class", "func"))
# A name assigned in the class after use reads the global first.
y = "global y"
def h():
    y = "local y"
    class Q:
        print_y = y
        y = "class y"
    return Q
assert_eq(h().print_y, "global y")

assert_syntax_error("def f():\n    x = 1\n    global x\n")
assert_syntax_error("def f():\n    nonlocal q\n")
assert_syntax_error("nonlocal x\n")
assert_syntax_error("def f(a):\n    global a\n")
assert_syntax_error("def f():\n    x = 1\n    def g():\n        print(x)\n        nonlocal x\n")
assert_syntax_error("def f():\n    global x\n    nonlocal x\n")

# del makes a name unbound; deleting a free variable then reading raises NameError.
def deleter():
    a = 1
    def inner(): return a
    del a
    return inner
assert_raises(NameError, deleter())

# Exception targets are deleted at the end of the except clause.
try:
    raise ValueError
except ValueError as caught:
    pass
assert_raises(NameError, run, "try:\n    1/0\nexcept ZeroDivisionError as e:\n    pass\ne\n")

# Names bound by import, for, with, def, class, walrus.
def binders():
    for a in [1]: pass
    with open.__class__ if False else _cm() as b: pass
    def c(): pass
    class d: pass
    (e := 5)
    return sorted(locals())
class _cm:
    def __enter__(self): return 1
    def __exit__(self, *a): pass
assert_eq(binders(), ["a", "b", "c", "d", "e"])

# builtins are found last; a module global shadows them.
ns = run("len = lambda x: 'mine'\nr = len([1])\n")
assert_eq(ns["r"], "mine")
assert_eq(run("del __builtins__\n" if False else "r = abs(-1)\n")["r"], 1)
# exec with explicit globals adds __builtins__.
g = {}
exec("z = 1", g)
assert_true("__builtins__" in g)
# Locals in exec/eval with separate mappings.
l = {}
exec("w = 2\ndef f(): return w", {}, l)
assert_raises(NameError, l["f"])
