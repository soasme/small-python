# spec: PLS-315 8.3.1
# description: a name an import binds may be declared global after it in
# the same scope; any other binding, use or annotation before the
# declaration is an error.
from harness import *

for source in ["def f():\n    import x\n    global x", "def f():\n    from m import x\n    global x", "def f():\n    import a.b\n    global a",
               "def f():\n    import x as y\n    global y", "class C:\n    import x\n    global x",
               "def g():\n    x = 1\n    def f():\n        import x\n        nonlocal x"]:
    compile(source, "s", "exec")
for source, message in [("def f():\n    import x\n    x = 1\n    global x", "name 'x' is assigned to before global declaration"),
                        ("def f():\n    x = 1\n    import x\n    global x", "name 'x' is assigned to before global declaration"),
                        ("def f():\n    import x\n    print(x)\n    global x", "name 'x' is used prior to global declaration"),
                        ("def f():\n    import x\n    x: int\n    global x", "annotated name 'x' can't be global"),
                        ("def f(x):\n    import x\n    global x", "name 'x' is parameter and global"),
                        ("def f():\n    import x\n    nonlocal x", "no binding for nonlocal 'x' found")]:
    assert_eq(assert_syntax_error(source).msg, message)

def run():
    import harness
    global harness
    return harness.assert_eq
assert_eq(run(), assert_eq)
assert_eq(harness.assert_eq, assert_eq)
