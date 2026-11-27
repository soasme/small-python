# spec: PLS-315 14.7
# description: a del statement deletes any number of targets from left to
# right, however many a target list holds; a starred target among them,
# at any depth, is "cannot delete starred".
from harness import assert_eq, assert_raises

names = ["x%d" % i for i in range(300)]
space = dict.fromkeys(names, 1)
space["y"] = 2
exec("del " + ", ".join(names), space)
assert_eq([name for name in space if name != "__builtins__"], ["y"])
nested = {"a": 1, "b": 2}
exec("del (a, [b])", nested)
assert_eq([name for name in nested if name != "__builtins__"], [])
for source in ["del " + ", ".join(names[:299]) + ", *z", "del [a, (b, [*c])]"]:
    error = assert_raises(SyntaxError, lambda: compile(source, "s", "exec"))
    assert_eq(error.msg, "cannot delete starred")
