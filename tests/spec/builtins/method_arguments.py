# spec: PLS-315 7.4.4, 7.3, 13.3.2
# description: Argument counts of built-in methods, and the messages for a missing special method.
from harness import *

def check(message, function, *args):
    assert_raises(TypeError, function, *args, message=message)

check("expected 0 arguments, got 1", iter([]).__next__, 1)
check("splitlines() takes at most 1 argument (2 given)", "a".splitlines, 1, 2)
check("sort() takes at most 2 arguments (3 given)", [].sort, 1, 2, 3)
check("index expected at least 1 argument, got 0", [].index)
check("range.index() takes exactly one argument (2 given)", range(3).index, 1, 2)
check("insert expected 2 arguments, got 1", [].insert, 1)
check("pop expected at most 1 argument, got 2", [].pop, 1, 2)
check("pop expected at least 1 argument, got 0", {}.pop)
check("setdefault expected at least 1 argument, got 0", {}.setdefault)
check("get expected at most 2 arguments, got 3", {}.get, 1, 2, 3)
check("update expected at most 1 argument, got 2", {}.update, 1, 2)
check("startswith expected at least 1 argument, got 0", "a".startswith)
check("find expected at most 3 arguments, got 4", "a".find, 1, 2, 3, 4)
check("__get__ expected at least 1 argument, got 0", super(int, 1).__get__)
check("throw expected at least 1 argument, got 0", (x for x in []).throw)
generator = (x for x in [])
check("generator.send() takes exactly one argument (0 given)", generator.send)
check("generator.close() takes no arguments (1 given)", generator.close, 1)
check("throw expected at most 3 arguments, got 4", generator.throw, 1, 2, 3, 4)
async def agen():
    yield 1
check("athrow expected at least 1 argument, got 0", agen().athrow)
check("async_generator.asend() takes exactly one argument (0 given)", agen().asend)
async def coroutine(): pass
running = coroutine()
check("coroutine.send() takes exactly one argument (0 given)", running.send)
check("throw expected at least 1 argument, got 0", running.__await__().throw)
running.close()

# A missing special method names the operation.
check("'int' object is not reversible", reversed, 3)
def subscript(x): return x[0]
def store(x): x[0] = 1
def delete(x): del x[0]
check("'int' object is not subscriptable", subscript, 3)
check("'int' object does not support item assignment", store, 3)
check("'int' object does not support item deletion", delete, 3)

# Set methods name their defining type and take positional arguments only.
for t in (set, frozenset):
    owner = t.__name__
    s = t()
    for name in ("isdisjoint", "issubset", "issuperset", "symmetric_difference"):
        check(f"{owner}.{name}() takes exactly one argument (0 given)", getattr(s, name))
        check(f"{owner}.{name}() takes exactly one argument (2 given)", getattr(s, name), 1, 2)
    check(f"{owner}.copy() takes no arguments (1 given)", s.copy, 1)
    check(f"{owner}.union() takes no keyword arguments", lambda: s.union(x=1))
    check(f"{owner}.issubset() takes no keyword arguments", lambda: s.issubset(x=1))
for name in ("add", "discard", "remove", "symmetric_difference_update"):
    check(f"set.{name}() takes exactly one argument (0 given)", getattr(set(), name))
    check(f"set.{name}() takes exactly one argument (3 given)", getattr(set(), name), 1, 2, 3)
for name in ("pop", "clear"):
    check(f"set.{name}() takes no arguments (1 given)", getattr(set(), name), 1)
check("set.add() takes no keyword arguments", lambda: set().add(x=1))
check("descriptor 'add' for 'set' objects doesn't apply to a 'int' object", set.add, 1, 2)

# Class methods name the class they are called on.
class SubDict(dict): pass
class SubBytes(bytes): pass
check("bytes.fromhex() takes exactly one argument (0 given)", bytes.fromhex)
check("bytearray.fromhex() takes exactly one argument (0 given)", bytearray.fromhex)
check("float.fromhex() takes exactly one argument (2 given)", float.fromhex, 1, 2)
check("SubBytes.fromhex() takes exactly one argument (0 given)", SubBytes.fromhex)
check("fromkeys expected at least 1 argument, got 0", frozendict.fromkeys)
check("fromkeys expected at most 2 arguments, got 3", dict.fromkeys, 1, 2, 3)
check("SubDict.fromkeys() takes no keyword arguments", lambda: SubDict.fromkeys(x=1))
check("float.fromhex() takes no keyword arguments", lambda: float.fromhex(x=1))
assert_eq((type(SubDict.fromkeys("a")), SubBytes.fromhex("41"), dict.fromkeys("a", 1)), (SubDict, b"A", {"a": 1}))

# Keyword-capable parameters: the counts, then required positional-only
# parameters, then required parameters by name, then unknown names.
check("split() takes at most 2 keyword arguments (3 given)", lambda: "abc".split(sep="b", maxsplit=1, x=2))
check("split() takes at most 2 arguments (3 given)", lambda: "abc".split("b", maxsplit=1, x=2))
check("eval() takes at least 1 positional argument (0 given)", lambda: eval(globals={}))
check("exec() takes at least 1 positional argument (0 given)", lambda: exec(source="x"))
Module = type(__import__("harness"))
check("module() missing required argument 'name' (pos 1)", lambda: Module(nam="x"))
check("argument for module() given by name ('name') and position (1)", lambda: Module("m", name="x"))
check("__lazy_import__() takes at most 5 arguments (6 given)", lambda: __lazy_import__("x", None, None, None, 0, name="y"))
check("__lazy_import__() got an unexpected keyword argument 'bogus'", lambda: __lazy_import__("x", bogus=1))

# Built-in functions word a wrong argument count by their argument parser.
check("globals() takes no arguments (1 given)", globals, 1)
check("locals() takes no arguments (2 given)", locals, 1, 2)
check("pow() missing required argument 'base' (pos 1)", pow)
check("pow() missing required argument 'exp' (pos 2)", pow, 1)
check("pow() takes at most 3 arguments (4 given)", pow, 1, 2, 3, 4)
check("__import__() missing required argument 'name' (pos 1)", __import__)
check("__import__() takes at most 5 arguments (6 given)", __import__, *"abcdef")
check("bytes() takes at most 3 arguments (4 given)", bytes, 1, 2, 3, 4)
check("complex() takes at most 2 arguments (3 given)", complex, 1, 2, 3)
check("sum() takes at least 1 positional argument (0 given)", sum)
check("sum() takes at most 2 arguments (3 given)", sum, 1, 2, 3)
check("eval() takes at least 1 positional argument (0 given)", eval)
check("exec() takes at least 1 positional argument (0 given)", exec)
check("eval() takes at most 3 arguments (4 given)", eval, "1", None, None, None)
check("exec() takes at most 3 positional arguments (4 given)", exec, "1", None, None, None)
check("exec() takes at most 4 arguments (5 given)", exec, "1", None, None, None, None)
check("eval() takes at most 3 arguments (5 given)", lambda: eval("1", None, None, None, globals=None))
check("exec() takes at most 4 arguments (5 given)", lambda: exec("1", None, None, None, globals=None))
check("exec() takes at most 3 positional arguments (4 given)", lambda: exec("1", None, None, None))
