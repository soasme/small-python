# spec: PLS-315 28.1
# description: a function made from a module's or eval()'s code takes no
# arguments and runs that code in its globals, which a call from inside a
# comprehension or a generator does too: definitions, global statements,
# loops and docstrings act there, an exception propagates, and the call
# gives None, or an eval expression's value.
from harness import assert_eq
FunctionType = type(lambda: 0)
g = {"y": 2, "log": []}
def run(f):
    try: r = f()
    except Exception as e: r = (type(e).__name__, str(e))
    return r
codes = ["log.append(y)", "x = 1", "global z; z = 5", "def q(): return y\nlog.append(q())", "'doc'\nlog.append(__doc__)",
         "raise KeyError('k')", "for i in range(3): log.append(i)", "def gen():\n    yield 1\nlog.append(list(gen()))", "a: int = 3\nlog.append(__annotations__)",
         "import harness_none_such", "return_value = [i for i in range(2)]"]
fs = [FunctionType(compile(s, "<m>", "exec"), g) for s in codes]
out = [run(f) for f in fs]
out.append(run(lambda: FunctionType(compile("y * 10", "<e>", "eval"), g)()))
out.append(run(lambda: FunctionType(compile("[y for _ in range(2)]", "<e>", "eval"), g)()))
out.append(run(lambda: FunctionType(compile("1/0", "<e>", "eval"), g)()))
out.append(run(lambda: FunctionType(compile("x = 7", "<s>", "single"), g)()))
out.append(run(lambda: FunctionType(compile("None", "<s>", "single"), g)()))
out.append(run(lambda: fs[0](1)))
out.append(run(lambda: fs[0](a=1)))
out.append(run(lambda: [f() for f in fs[:2]]))
def gen():
    yield fs[0]()
    yield FunctionType(compile("y + 1", "<e>", "eval"), g)()
out.append(list(gen()))
out.append(sorted(k for k in g if k != '__builtins__'))
out.append(g["log"])
assert_eq(out, [None, None, None, None, None, ('KeyError', "'k'"), None, None, ('NameError', "name '__annotations__' is not defined"), ('ModuleNotFoundError', "No module named 'harness_none_such'"), None, 20, [2, 2], ('ZeroDivisionError', 'division by zero'), None, None, ('TypeError', '<module>() takes 0 positional arguments but 1 was given'), ('TypeError', "<module>() got an unexpected keyword argument 'a'"), [None, None], [None, 3], ['__annotate__', '__conditional_annotations__', '__doc__', 'a', 'gen', 'i', 'log', 'q', 'return_value', 'x', 'y', 'z'], [2, 2, 'doc', 0, 1, 2, [1], 2, 2]])
