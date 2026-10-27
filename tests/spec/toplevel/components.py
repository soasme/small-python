# spec: reference/toplevel_components.html
# description: Complete programs, file input, interactive input, and expression input through compile, exec, and eval.
from harness import *

# The main program runs as module __main__ with builtins available.
assert_eq(__name__, "__main__")
import builtins
assert_is(builtins.len, len)

# File input: a sequence of statements, compiled in 'exec' mode.
code = compile("x = 1\nif x:\n    y = x + 1\n", "<file>", "exec")
assert_eq((code.co_filename, code.co_name), ("<file>", "<module>"))
namespace = {}
assert_is(exec(code, namespace), None)
assert_eq((namespace["x"], namespace["y"]), (1, 2))
assert_compiles("")
assert_compiles("# only a comment")
assert_compiles("\n\n\n")

# Expression input: eval() takes one expression list; leading whitespace is stripped.
assert_eq((eval("1, 2"), eval("  3 + 4"), eval("\t5"), eval("(lambda: 6)()")), ((1, 2), 7, 5, 6))
assert_syntax_error("x = 1", "eval")
assert_syntax_error("pass", "eval")
assert_syntax_error("1; 2", "eval")
assert_syntax_error("", "eval")
assert_eq(eval(compile("2 ** 8", "<expr>", "eval")), 256)
assert_eq(eval(b"1 + 1"), 2)
# eval accepts a trailing newline and comments.
assert_eq(eval("1 + 1\n"), 2)
assert_eq(eval("1  # comment"), 1)

# Interactive input: 'single' mode compiles one statement, possibly compound.
assert_compiles("x = 1", "single")
assert_compiles("if 1:\n    pass\n", "single")
assert_syntax_error("x = 1\ny = 2\n", "single")
ns = {}
exec(compile("z = 5", "<stdin>", "single"), ns)
assert_eq(ns["z"], 5)

# eval and exec take globals and locals; locals may be any mapping.
class Mapping:
    def __init__(self): self.store = {"a": 1}
    def __getitem__(self, key): return self.store[key]
    def __setitem__(self, key, value): self.store[key] = value
    def keys(self): return self.store.keys()
mapping = Mapping()
exec("b = a + 1", {}, mapping)
assert_eq((eval("a + b", {}, mapping), mapping.store), (3, {"a": 1, "b": 2}))
assert_raises(TypeError, eval, "1", [])
assert_raises(TypeError, eval, "1", {}, 1)
# Missing __builtins__ is inserted into the globals.
g = {}
eval("1", g)
assert_true("__builtins__" in g)
# A custom __builtins__ dict controls builtin lookups.
assert_eq(eval("len", {"__builtins__": {"len": "mine"}}), "mine")
# Functions defined by exec use its globals.
g = {"value": 10}
exec("def get(): return value", g)
g["value"] = 20
assert_eq(g["get"](), 20)
# exec with separate locals: definitions go into locals; class bodies see them.
loc = {}
exec("v = 1\ndef f(): return v\n", {}, loc)
assert_eq(sorted(loc), ["f", "v"])
assert_raises(NameError, loc["f"])

# compile flags and dont_inherit; optimize level controls __debug__ and assert.
assert_eq(eval(compile("__debug__", "<x>", "eval")), True)
ns = {}
exec(compile("assert False\nok = 1", "<x>", "exec", optimize=1), ns)
assert_eq(ns["ok"], 1)
assert_eq(eval(compile("__debug__", "<x>", "eval", optimize=1)), False)
assert_raises(ValueError, compile, "1", "<x>", "eval", flags=1 << 30)
# Source with a null byte is rejected.
assert_raises(SyntaxError, compile, "a\0", "<x>", "exec")
# An encoding declaration in bytes source is honored.
ns = {}
exec(b"# -*- coding: latin-1 -*-\ns = '\xe9'\n", ns)
assert_eq(ns["s"], "\xe9")
# The main module is in sys.modules under "__main__", with globals as its namespace.
import sys
assert_is(sys.modules["__main__"].__dict__, globals())
# The main module has the standard module attributes.
for name in ("__spec__", "__loader__", "__package__", "__doc__"):
    assert_true(name in globals())
