# Replays FunctionDefs.tla: each case defines the spec's function, lambda,
# or class with logging decorators, defaults, bases, and body (or runs one of
# the spec's sources), and compares the outcome and the log with the
# model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

PRE = """log = []
def t(v):
    log.append(v if isinstance(v, str) else v.__name__ if isinstance(v, type) else repr(v))
    return v
def deco(i):
    log.append('eval d%d' % i)
    def apply(f):
        log.append('apply d%d' % i)
        return f
    return apply
class B1: pass
class B2: pass
"""
SOURCES = {
    "mutable_default": "def f(a=[]):\n    a.append(1)\n    return a\nf()\nresult = f()",
    "default_once": "n = 0\ndef c():\n    global n\n    n += 1\n    return n\ndef f(a=c()): return a\nresult = (f(), f(), n)",
    "default_order_error": "def f(a=1, b): pass",
    "kwonly_no_default_ok": "def f(*, a, b=1): return (a, b)\nresult = f(a=0)",
    "duplicate_param": "def f(a, a): pass",
    "duplicate_kw_param": "def f(a, *, a): pass",
    "bare_star_end": "def f(a, *): pass",
    "slash_first": "def f(/, a): pass",
    "slash_after_star": "def f(*, a, /): pass",
    "two_slashes": "def f(a, /, b, /): pass",
    "two_stars": "def f(*a, *b): pass",
    "kwargs_not_last": "def f(**k, a): pass",
    "star_default": "def f(*a=1): pass",
    "return_default": "def f(): pass\nresult = f()",
    "docstring": "def f():\n    'doc'\nresult = (f.__doc__, f.__name__, f.__qualname__)",
    "no_docstring_expr": "def f():\n    x = 1\n    'not doc'\nresult = f.__doc__",
    "nested_qualname": "def f():\n    def g(): pass\n    return g\nresult = f().__qualname__",
    "method_qualname": "class C:\n    def m(self): pass\nresult = C.m.__qualname__",
    "generator_detect": "def f():\n    if False:\n        yield\nresult = type(f()).__name__",
    "return_in_class": "class C:\n    return 1",
    "return_outside": "return 1",
    "yield_outside": "yield 1",
    "def_is_assignment": "def f(): return 1\ng = f\ndef f(): return 2\nresult = (g(), f())",
    "decorator_expr": "result = []\n@(lambda f: (result.append(f.__name__), f)[1])\ndef f(): pass",
    "decorator_arbitrary": "@[lambda f: 'wrapped'][0]\ndef f(): pass\nresult = f",
    "lambda_basic": "result = (lambda x, y=2: x + y)(1)",
    "lambda_name": "f = lambda: 0\nresult = (f.__name__, f.__qualname__)",
    "lambda_statement": "f = lambda: x = 1",
    "lambda_annotation": "f = lambda x: int: x",
    "lambda_yield": "f = lambda: (yield)\nresult = type(f()).__name__",
    "lambda_late_binding": "fs = [lambda: i for i in range(3)]\nresult = [f() for f in fs]",
    "lambda_default_capture": "fs = [lambda i=i: i for i in range(3)]\nresult = [f() for f in fs]",
    "lambda_star_args": "result = (lambda *a, **k: (a, k))(1, b=2)",
    "lambda_posonly": "result = (lambda a, /, b: (a, b))(1, b=2)",
    "lambda_in_default": "def f(g=lambda: 5): return g()\nresult = f()",
    "lambda_cond": "result = (lambda: 1 if 0 else 2)()",
    "walrus_scope": "def f():\n    if (n := 3) > 2:\n        pass\n    return n\nresult = f()",
    "walrus_statement": "x := 1",
    "walrus_attr": "(a.b := 1)",
    "walrus_subscript": "(a[0] := 1)",
    "walrus_paren_ok": "(x := 1)\nresult = x",
    "walrus_in_call": "def f(a): return a\nresult = (f(x := 5), x)",
    "walrus_kwarg": "f(a=x := 1)",
    "walrus_default": "def f(a=(x := 4)): return a\nresult = (f(), x)",
    "walrus_lambda": "f = lambda: (y := 7)\nresult = f()",
    "walrus_precedence": "result = (y := 1 + 2, y)",
    "walrus_unparenthesized_tuple": "result = (y := 1, 2)",
    "walrus_in_fstring": "result = f'{(z := 3)}' + str(z)",
    "walrus_comprehension_class": "class C:\n    [(q := 1) for _ in range(1)]",
    "walrus_nonlocal": "def f():\n    x = 0\n    def g():\n        nonlocal x\n        (x := 9)\n    g()\n    return x\nresult = f()",
    "walrus_global_in_comp": "def f():\n    [(gw := i) for i in range(2)]\n    return gw\nresult = f()",
    "walrus_rebind_iter_nested": "[[(i := 0) for j in range(1)] for i in range(1)]",
    "walrus_keyword_name": "(True := 1)",
}


def source(p):
    if "case" in p:
        return SOURCES[p["case"]]
    decorators = "".join("@deco(%d)\n" % i for i in range(1, p["decorators"] + 1))
    if p["kind"] == "class":
        args = ["t(B%d)" % i for i in range(1, p["positional"] + 1)] + ["metaclass=t(type)"] * p["keyword"]
        return decorators + "class C(%s):\n    log.append('body')" % ", ".join(args)
    params = ["a%d=t(%d)" % (i, i) for i in range(1, p["positional"] + 1)]
    if p["keyword"]:
        params += ["*"] + ["k%d=t(%d)" % (j, 10 + j) for j in range(1, p["keyword"] + 1)]
    if p["kind"] == "lambda":
        return "f = lambda %s: 0" % ", ".join(params)
    return decorators + "def f(%s): pass" % ", ".join(params)


def outcome(p):
    namespace = {}
    try:
        exec(compile(PRE + source(p), "<definition>", "exec"), namespace)
        result = "ok" if "case" not in p else repr(namespace.get("result"))
    except SyntaxError as error:
        result = "%s: %s" % (type(error).__name__, error.msg)
    except Exception as error:
        result = "%s: %s" % (type(error).__name__, error)
    return (result, tuple(namespace.get("log", ())) if "case" not in p else ())


check_programs(outcome)
