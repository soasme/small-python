# spec: PLS-315 28.1, 28.6, 16.2, 9.1
# description: Functions built from code objects with any closure cells and globals, functions of module and eval code, and code replacement with other free variables.
from harness import *

FunctionType = type(lambda: None)
CellType = type((lambda x: lambda: x)(0).__closure__[0])

def outer_a():
    a = 1
    def get(): return a
    def put(v):
        nonlocal a
        a = v
    return get, put
def outer_b():
    b = 2
    def get(): return b
    return get
def template():
    a = b = None
    def f(n):
        nonlocal a
        a = a + n
        def g(): return a, b
        return a + b, g
    return f
code = template().__code__
assert_eq(code.co_freevars, ("a", "b"))

# Cells from unrelated scopes: the new function shares each variable.
get_a, put_a = outer_a()
get_b = outer_b()
f = FunctionType(code, globals(), "f", None, (get_a.__closure__[0], get_b.__closure__[0]))
assert_eq(f(10)[0], 13)
assert_eq(get_a(), 11)
assert_eq(f.__closure__, (get_a.__closure__[0], get_b.__closure__[0]))
put_a(100)
assert_eq(f(1)[0], 103)
inner = f(0)[1]
assert_eq(inner(), (101, 2))
assert_eq(inner.__closure__[0].cell_contents, 101)

# A new cell mixed with a defining scope's cell.
fresh = CellType(5)
h = FunctionType(code, globals(), "h", None, (get_a.__closure__[0], fresh))
assert_eq((h(1)[0], fresh.cell_contents, get_a()), (107, 5, 102))

# Other globals than those of the cells' scope.
def uses_global():
    a = 1
    def k(): return a, G
    return k
G = "main"
k = uses_global()
k2 = FunctionType(k.__code__, {"G": "other"}, "k2", None, k.__closure__)
assert_eq((k(), k2(), k2.__globals__["G"]), ((1, "main"), (1, "other"), "other"))

# An empty cell reads as an unbound free variable until it is filled.
empty = CellType()
z = FunctionType(code, globals(), "z", None, (empty, fresh))
e = assert_raises(NameError, z, 1)
assert_eq(str(e), "cannot access free variable 'a' where it is not associated with a value in enclosing scope")
empty.cell_contents = 3
assert_eq((z(1)[0], empty.cell_contents), (9, 4))
del empty.cell_contents
assert_raises(NameError, z, 1)

# locals() shows the free variable; del of a nonlocal empties the cell.
def show():
    a = 7
    def q(): return locals(), a
    return q
assert_eq(FunctionType(show().__code__, {}, "q", None, (CellType(9),))(), ({"a": 9}, 9))
def deleting():
    a = 1
    def d():
        nonlocal a
        del a
    return d
c9 = CellType(9)
FunctionType(deleting().__code__, {}, "d", None, (c9,))()
assert_eq(str(assert_raises(ValueError, lambda: c9.cell_contents)), "Cell is empty")

# Assigning code with other free variables keeps the function's cells.
def mk():
    a = 1
    def inner(): return a
    return inner
def mk2():
    b = 2
    def inner2(): return b * 100
    return inner2
i = mk()
i.__code__ = mk2().__code__
assert_eq((i(), i.__closure__[0].cell_contents), (100, 1))

# Functions of module and eval code take no arguments and run in their globals.
g = {"y": 2}
log = []
g["log"] = log
for source in ["log.append(y)", "x = 1", "global z; z = 5", "def q(): return y\nlog.append(q())"]:
    co = compile(source, "<m>", "exec")
    m = FunctionType(co, g)
    assert_eq(m(), None)
    assert_eq((m.__name__, m.__qualname__, m.__code__ is co, m.__defaults__, m.__closure__, m.__globals__ is g),
              ("<module>", "<module>", True, None, None, True))
assert_eq((log, g["x"], g["z"]), ([2, 2], 1, 5))
m = FunctionType(co, g)
assert_eq(str(assert_raises(TypeError, m, 1)), "<module>() takes 0 positional arguments but 1 was given")
assert_eq(str(assert_raises(TypeError, m, 1, 2)), "<module>() takes 0 positional arguments but 2 were given")
assert_eq(str(assert_raises(TypeError, lambda: m(a=1))), "<module>() got an unexpected keyword argument 'a'")
assert_eq(FunctionType(compile("y * 10", "<e>", "eval"), g)(), 20)
named = FunctionType(compile("class C: pass\nresult = C.__qualname__, C.__module__", "<m>", "exec"), {"__name__": "modx"}, "named")
assert_eq((named.__name__, named.__qualname__, named(), named.__globals__["result"]), ("named", "<module>", None, ("C", "modx")))
def target(): pass
target.__code__ = compile("log.append('via target')", "<m>", "exec")
target()
assert_eq(log[-1], "via target")

# A function of a generator expression's code takes the iterable as '.0' and returns the generator.
gen_code = (x * 2 for x in range(3)).gi_code
assert_eq((gen_code.co_argcount, gen_code.co_varnames, gen_code.co_nlocals), (1, (".0", "x"), 2))
gx = FunctionType(gen_code, {})
assert_eq((gx.__name__, gx.__qualname__, list(gx([1, 2])), list(gx(iter("ab")))), ("<genexpr>", "<genexpr>", [2, 4], ["aa", "bb"]))
made = gx(iter([5]))
assert_eq((made.__name__, made.__qualname__, made.gi_code is gen_code), ("<genexpr>", "<genexpr>", True))
assert_eq(str(assert_raises(TypeError, gx)), "<genexpr>() missing 1 required positional argument: '.0'")
assert_eq(str(assert_raises(TypeError, gx, iter([1]), 2)), "<genexpr>() takes 1 positional argument but 2 were given")
assert_eq(str(assert_raises(TypeError, lambda: gx(a=1))), "<genexpr>() got an unexpected keyword argument 'a'")
def with_free(k):
    return (x + k for x in ())
free_code = with_free(1).gi_code
assert_eq((free_code.co_freevars, free_code.co_varnames), (("k",), (".0", "x")))
assert_eq(list(FunctionType(free_code, {}, None, None, (CellType(10),))(iter([1, 2]))), [11, 12])
def renamed_gen(): pass
renamed_gen.__code__ = gen_code
made = renamed_gen([3])
assert_eq((made.__name__, made.__qualname__, list(made)), ("renamed_gen", "renamed_gen", [6]))
assert_eq(str(assert_raises(TypeError, renamed_gen)), "renamed_gen() missing 1 required positional argument: '.0'")

# An asynchronous generator expression's code makes an asynchronous generator.
class Counter:
    def __init__(self): self.n = 0
    def __aiter__(self): return self
    async def __anext__(self):
        self.n += 1
        if self.n > 2: raise StopAsyncIteration
        return self.n
async def make_async():
    return (x * 10 async for x in Counter())
def run_coroutine(coroutine):
    try: coroutine.send(None)
    except StopIteration as stop: return stop.value
async_code = run_coroutine(make_async()).ag_code
assert_eq((async_code.co_varnames, async_code.co_flags & 0x200, async_code.co_argcount), ((".0", "x"), 0x200, 1))
agx = FunctionType(async_code, {})(Counter())
async def collect(): return [x async for x in agx]
assert_eq((type(agx).__name__, run_coroutine(collect())), ("async_generator", [10, 20]))
