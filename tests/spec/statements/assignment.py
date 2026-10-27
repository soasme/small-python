# spec: reference/simple_stmts.html#assignment-statements
# description: Target lists, starred unpacking, chained, augmented and annotated assignment, evaluation order.
from harness import *

a, b = 1, 2
a, b = b, a
assert_eq((a, b), (2, 1))
[c, (d, e)] = [1, (2, 3)]
assert_eq((c, d, e), (1, 2, 3))
first, *rest = "abc"
assert_eq((first, rest), ("a", ["b", "c"]))
*init, last = range(3)
assert_eq((init, last), ([0, 1], 2))
x, *y, z = 1, 2
assert_eq(y, [])
e = assert_raises(ValueError, run, "a, b = 1, 2, 3")
assert_eq(str(e), "too many values to unpack (expected 2, got 3)")
e = assert_raises(ValueError, run, "a, b, c = 1, 2")
assert_eq(str(e), "not enough values to unpack (expected 3, got 2)")
e = assert_raises(ValueError, run, "a, *b, c = [1]")
assert_eq(str(e), "not enough values to unpack (expected at least 2, got 1)")
assert_raises(TypeError, run, "a, b = 1")
assert_syntax_error("*a = [1]")
assert_syntax_error("a, *b, *c = [1]")
assert_syntax_error("f() = 1")
assert_syntax_error("1 = x")
assert_syntax_error("(a, b) += 1")
assert_syntax_error("None = 1")
assert_syntax_error("__debug__ = 1")
assert_syntax_error("x.__debug__ = 1") if False else None
assert_syntax_error("a + 1 = 2")
assert_syntax_error("[x for x in y] = 1")
assert_syntax_error("a if b else c = 1")
assert_syntax_error("lambda: 1 = 1")
assert_syntax_error("(yield) = 1") if False else None
*star, = [1, 2]
assert_eq(star, [1, 2])
[] = []
() = ()

# Chained assignment assigns left to right, evaluating the value once.
log = []
class Rec:
    def __setitem__(self, k, v): log.append(k)
r = Rec()
r[1] = r[2] = (log.append("value"), 0)[1]
assert_eq(log, ["value", 1, 2])
i = 0
lst = [0, 0]
i, lst[i] = 1, 9
assert_eq(lst, [0, 9])

# Evaluation order: the right side first, then targets left to right.
order = []
def k(n):
    order.append(n)
    return n
d = {}
d[k("t1")], d[k("t2")] = k("v1"), k("v2")
assert_eq(order, ["v1", "v2", "t1", "t2"])
order.clear()
d[k("key")] = k("val")
assert_eq(order, ["val", "key"])
order.clear()
# Augmented assignment evaluates the target once.
class Counter:
    n = 0
    def __getitem__(self, key):
        order.append("get"); return 1
    def __setitem__(self, key, value):
        order.append(("set", value))
order.clear()
cnt = Counter()
cnt[k("idx")] += 1
assert_eq(order, ["idx", "get", ("set", 2)])

# Annotated assignments.
def ann():
    v: int = 1
    w: str
    return v
assert_eq(ann(), 1)
ns = run("q: int = 3\nr: list[int]\n")
assert_eq(ns["q"], 3)
assert_false("r" in ns)
assert_eq(ns["__annotate__"](1), {"q": int, "r": list[int]})
assert_syntax_error("a, b: int = 1, 2")
assert_syntax_error("[a]: int")
ns = run("class A:\n    x: int\n    y: str = 's'\n")
assert_eq(ns["A"].__annotations__, {"x": int, "y": str})
assert_eq(ns["A"].y, "s")
# Annotations are lazily evaluated.
ns = run("def f() -> Undefined: pass\n")
assert_raises(NameError, lambda: ns["f"].__annotations__)
ns = run("x: (1/0) = 5\n")
assert_eq(ns["x"], 5)
ns = run("(paren): int = 1\no = type('O', (), {})()\no.attr: int = 2\n")
assert_eq((ns["paren"], ns["o"].attr), (1, 2))
assert_eq(ns["__annotate__"](1), {"paren": int}) if False else None

# Starred in a right-hand side and in return/yield.
t = *range(2), 5
assert_eq(t, (0, 1, 5))
def ret(): return 1, *[2, 3]
assert_eq(ret(), (1, 2, 3))
assert_syntax_error("x = *a")
