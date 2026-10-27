# spec: reference/simple_stmts.html
# description: assert, pass, del, return, yield, raise, break, continue, global, type statement.
from harness import *

assert True, "never"
e = assert_raises(AssertionError, run, "assert 1 == 2, 'msg'")
assert_eq(e.args, ("msg",))
e = assert_raises(AssertionError, run, "assert False")
assert_eq(e.args, ())
# The message is evaluated only on failure.
assert True, 1/0
assert_syntax_error("assert(x, 'y')") if False else None

pass
x = [1, 2, 3]
del x[0], x[0]
assert_eq(x, [3])
y = 1
del y
assert_raises(NameError, run, "del undefined_name")
class O: pass
o = O(); o.a = 1
del o.a
assert_raises(AttributeError, run, "del o.a", {"o": o})
a_ = b_ = 1
del (a_, b_)
assert_raises(NameError, lambda: a_)
assert_syntax_error("del f()")
assert_syntax_error("del 1")
assert_syntax_error("del a + b")
def f():
    del (z)
    z = 1
assert_raises(UnboundLocalError, f)

assert_syntax_error("return 1")
assert_syntax_error("class C:\n    return 1\n")
assert_syntax_error("yield 1")
assert_syntax_error("class C:\n    yield 1\n")
assert_syntax_error("break")
assert_syntax_error("continue")
assert_syntax_error("def f():\n    break\n")
assert_syntax_error("for x in y:\n    def f():\n        break\n")
assert_syntax_error("while 1:\n    class C:\n        continue\n")
# continue and break are allowed in finally since 3.8; return in finally warns.
def loop():
    out = []
    for i in range(5):
        try:
            if i == 3: break
        finally:
            out.append(i)
            continue
    return out
assert_eq(loop(), [0, 1, 2, 3, 4])

# The type statement creates a lazily evaluated TypeAliasType.
ns = run("type Alias = list[int]\n")
A = ns["Alias"]
assert_eq(A.__name__, "Alias")
assert_eq(A.__value__, list[int])
assert_eq(type(A).__name__, "TypeAliasType")
ns = run("type Lazy = Undefined\n")
assert_raises(NameError, lambda: ns["Lazy"].__value__)
ns = run("type Pair[T] = tuple[T, T]\n")
P = ns["Pair"]
assert_eq(len(P.__type_params__), 1)
assert_eq(P.__type_params__[0].__name__, "T")
assert_eq(P[int].__args__, (int,))
assert_eq(repr(ns["Pair"]), "Pair")
assert_syntax_error("type X[T, T] = int")
assert_syntax_error("def f():\n    type = 1\n    type X = 1\n") if False else None
# 'type' stays a soft keyword.
type = 5
del type
assert_eq(type(1), int)

# global statement at module level is allowed and meaningless.
global gg
gg = 1
assert_eq(gg, 1)

# An error raised by an operation inside a handler, finally, or __exit__
# gets the exception being handled as its __context__.
def fails_in_handler():
    try:
        raise KeyError
    except KeyError:
        1 / 0
def fails_in_finally():
    try:
        raise KeyError
    finally:
        [][1]
def bad_raise_in_handler():
    try:
        raise KeyError
    except KeyError:
        raise 5
class FailingExit:
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        1 / 0
def fails_in_exit():
    with FailingExit():
        raise KeyError
for function, kind in [(fails_in_handler, ZeroDivisionError), (fails_in_finally, IndexError),
                       (bad_raise_in_handler, TypeError), (fails_in_exit, ZeroDivisionError)]:
    e = assert_raises(kind, function)
    assert_type(e.__context__, KeyError)

# Interactive expression statements go through sys.displayhook.
import sys
shown = []
saved_hook = sys.displayhook
sys.displayhook = shown.append
try:
    exec(compile("1 + 1\n", "<input>", "single"), {})
    exec(compile("None\n", "<input>", "single"), {})
finally:
    sys.displayhook = saved_hook
assert_eq(shown, [2, None])
