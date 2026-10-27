# spec: PLS-315 8.3, 8.4, 14.14
# description: global and nonlocal declarations and their early errors.
from harness import *

g = "module"
def set_global():
    global g
    g = "set"
set_global()
assert_eq(g, "set")

def counter():
    n = 0
    def bump():
        nonlocal n
        n += 1
        return n
    return bump
bump = counter()
bump()
assert_eq(bump(), 2)

# global in a class scope applies to the class body only.
ns = run("x = 'm'\nclass C:\n    global x\n    x = 'c'\n    def f(self):\n        return x\n")
assert_eq(ns["x"], "c")
assert_false("x" in ns["C"].__dict__)
# nonlocal in a class scope refers to the enclosing function scope.
def make():
    v = 1
    class K:
        nonlocal v
        v = 2
    return v, "v" in K.__dict__
assert_eq(make(), (2, False))

def errors(source):
    return assert_syntax_error(source).msg
assert_eq(errors("def f(a):\n    global a\n"), "name 'a' is parameter and global")
assert_eq(errors("def o():\n    def f(a):\n        nonlocal a\n"), "name 'a' is parameter and nonlocal")
assert_eq(errors("def f():\n    x = 1\n    global x\n"), "name 'x' is assigned to before global declaration")
assert_eq(errors("def o():\n    x = 0\n    def f():\n        x = 1\n        nonlocal x\n"),
          "name 'x' is assigned to before nonlocal declaration")
assert_eq(errors("def f():\n    print(x)\n    global x\n"), "name 'x' is used prior to global declaration")
assert_eq(errors("def o():\n    x = 0\n    def f():\n        print(x)\n        nonlocal x\n"),
          "name 'x' is used prior to nonlocal declaration")
assert_eq(errors("def f():\n    x: int\n    global x\n"), "annotated name 'x' can't be global")
assert_eq(errors("def o():\n    x = 0\n    def f():\n        x: int\n        nonlocal x\n"),
          "annotated name 'x' can't be nonlocal")
assert_eq(errors("def o():\n    x = 0\n    def f():\n        global x\n        nonlocal x\n"),
          "name 'x' is nonlocal and global")
assert_eq(errors("nonlocal x\n"), "nonlocal declaration not allowed at module level")
assert_eq(errors("def f():\n    nonlocal x\n"), "no binding for nonlocal 'x' found")
assert_eq(errors("def f(a, a): pass\n"), "duplicate parameter 'a' in function definition")
assert_eq(errors("def f(a, *, a): pass\n"), "duplicate parameter 'a' in function definition")
assert_eq(errors("lambda a, a: 0\n"), "duplicate parameter 'a' in function definition")
assert_eq(errors("def f[T, T](): pass\n"), "duplicate type parameter 'T'")
assert_eq(errors("class C[T, T]: pass\n"), "duplicate type parameter 'T'")
# Repeating a declaration is allowed.
assert_compiles("def f():\n    global x, x\n    global x\n")
