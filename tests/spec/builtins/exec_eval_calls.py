# spec: PLS-315 19.3.14, 19.3.15, 19.3.10
# description: exec() runs source or a module's code in the given
# globals and locals, returning None, with the source's docstring as
# __doc__, its errors' tracebacks passing through a '<module>' frame of
# '<string>'; eval() returns an expression's value, ignoring leading
# spaces; both reach the caller's names, nest, and run inside functions
# and generators, a locals mapping's Python methods storing and reading,
# the first store an annotated module's __annotate__.
from harness import *

log = []

def tb_entries(e):
    out = []
    tb = e.__traceback__
    while tb:
        out.append((tb.tb_frame.f_code.co_name, tb.tb_frame.f_code.co_filename, tb.tb_lineno))
        tb = tb.tb_next
    return out[1:]

class Doubling(dict):
    def __setitem__(s, k, v):
        for _ in range(2): pass
        dict.__setitem__(s, k, v * 2)
    def __getitem__(s, k):
        for _ in range(2): pass
        return dict.__getitem__(s, k)

class Refusing(dict):
    def __setitem__(s, k, v):
        raise KeyError(k)

def run():
    g = {"log": log}
    out = [exec("x = 1\nfor i in range(3): log.append(i)\ny = x + 2", g), g["y"], eval("y * 10", g), eval("  1 + 2")]
    loc = {}
    exec("a = 5\nb = a * 2", g, loc)
    out.append(sorted(loc.items()))
    out.append(eval(compile("3 * 3", "<c>", "eval")))
    out.append((exec(compile("z = 4", "<c>", "exec"), g), g["z"]))
    out.append(eval(compile("w = 1", "<c>", "exec"), g))
    try: exec("1 / 0")
    except ZeroDivisionError as e: out.append(str(e))
    try: exec("q = 1\nr = 2\nraise KeyError(q)")
    except KeyError as e: out.append(tb_entries(e))
    try: eval("1 +")
    except SyntaxError as e: out.append(e.msg)
    exec('"doc"\nq = 1', g)
    out.append(g["__doc__"])
    def inner():
        v = 7
        return eval("v + 1")
    out.append(inner())
    out.append(eval("[i for i in range(3)]"))
    exec("def h(): return 42\nclass K:\n    w = 3", g)
    out.append((g["h"](), g["K"].w))
    def gen():
        yield eval("1 + 1")
        exec("for i in range(2): pass")
        yield 3
    out.append(list(gen()))
    out.append(eval("eval('2 * 3')"))
    m = Doubling()
    exec("a = 3\nb = a + 1", {}, m)
    out.append(sorted(m.items()))
    out.append(exec(""))
    try: exec("x: int = 1", {}, Refusing())
    except KeyError as e: out.append(e.args)
    return out

assert_eq(run(), [None, 3, 30, 3, [("a", 5), ("b", 10)], 9, (None, 4), None, "division by zero",
                  [("<module>", "<string>", 3)], "invalid syntax", "doc", 8, [0, 1, 2], (42, 3), [2, 3], 6,
                  [("a", 6), ("b", 14)], None, ("__annotate__",)])
assert_eq(log, [0, 1, 2])
