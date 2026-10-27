# spec: PLS-315 14.4, 16.6
# description: Annotated assignment evaluates the target's primary and the value, never the annotation at once.
from harness import *

log = []
def e(n, value=None):
    log.append(n)
    return n if value is None else value

# The annotation is not evaluated by the statement.
ns = run("x: undefined_name = 1\ny: also_undefined\n")
assert_eq(ns["x"], 1)
assert_false("y" in ns)
# It is recorded for the scope's __annotate__, evaluated on demand.
ns = run("x: int = 1\ny: str\nclass C:\n    a: int\n    b: list = []\n")
assert_eq(ns["__annotate__"](1), {"x": int, "y": str})
assert_eq(ns["C"].__annotations__, {"a": int, "b": list})
assert_eq(ns["C"].b, [])
assert_false(hasattr(ns["C"], "a"))
ns = run("x: undefined_name = 1\n")
assert_raises(NameError, ns["__annotate__"], 1)

# Attribute and subscript targets: the primary is evaluated even without a value.
class Obj:
    pass
o = Obj()
log.clear()
e(1, o).attr: e(99)
assert_eq(log, [1])
assert_false(hasattr(o, "attr"))
d = {}
log.clear()
e(1, d)[e(2, "k")]: e(99)
assert_eq(log, [1, 2])
assert_eq(d, {})
log.clear()
e(2, d)[e(3, "k")]: int = e(1, "v")
assert_eq(log, [1, 2, 3])
assert_eq(d, {"k": "v"})
# Only unparenthesized names are recorded.
ns = run("class C:\n    w: int\n    (x): int = 1\n    y.z: int = 2\n", {"y": Obj()})
assert_eq(ns["C"].__annotations__, {"w": int})
ns = run("class C:\n    (x): int = 1\n")
assert_eq(ns["C"].x, 1)

# An unparenthesized expression list value is a tuple.
t: tuple = 1, 2
assert_eq(t, (1, 2))
s: tuple = *[1], 2
assert_eq(s, (1, 2))

# In a function the annotation is never evaluated, and the name is local.
def f():
    z: undefined_name
    try:
        return z
    except NameError as e:
        return type(e).__name__
assert_eq(f(), "UnboundLocalError")
def g():
    w: undefined_name = 3
    return w
assert_eq(g(), 3)
assert_false("__annotate__" in g.__code__.co_names)

assert_eq(assert_syntax_error("[a, b]: int\n").msg, "only single target (not list) can be annotated")
assert_eq(assert_syntax_error("a, b: int\n").msg, "only single target (not tuple) can be annotated")
assert_eq(assert_syntax_error("(a, b): int\n").msg, "only single target (not tuple) can be annotated")
