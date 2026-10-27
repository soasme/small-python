# spec: PLS-315 19.3.14, 19.3.15, 9.3.4
# description: eval and exec give globals without __builtins__ the calling frame's builtins.
from harness import *

# At module level, the inserted value is the built-in namespace itself.
g = {}
exec("", g)
assert_type(g["__builtins__"], dict)
assert_is(g["__builtins__"]["len"], len)

# Code running with its own builtins passes them on, to exec and to eval.
own = {"exec": exec, "eval": eval, "len": len}
ns = {"__builtins__": own}
exec("inner = {}; exec('', inner); result = inner['__builtins__']", ns)
assert_is(ns["result"], own)
ns = {"__builtins__": own}
exec("inner = {}; eval('1', inner); result = inner['__builtins__']", ns)
assert_is(ns["result"], own)

# So a program that rebinds a built-in through exec changes only its own builtins.
ns = {"__builtins__": dict(own)}
exec("exec(\"__builtins__['len'] = 9\", {})", ns)
assert_eq(ns["__builtins__"]["len"], 9)
assert_is(own["len"], len)

# A given __builtins__ is kept.
g = {"__builtins__": {"x": 1}}
exec("y = x", g)
assert_eq(g["y"], 1)
