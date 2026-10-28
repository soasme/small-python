# Replays Future.tla: each case compiles the spec's source without
# inheriting this script's future features, runs it, and compares the
# result (or the exception and its message, without the location) with the
# model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

FA = "from __future__ import annotations\n"
SOURCES = {
    "stringized": FA + "def f(x: undefined, *a: int, **k: 'q') -> None: pass\nresult = f.__annotations__",
    "eager_without": "def f(x: undefined): pass\nresult = f.__annotations__",
    "class": FA + "class C:\n    x: undefined\n    y: int = 1\nresult = C.__annotations__",
    "module": FA + "x: undefined\nresult = __annotations__",
    "unparse": FA + "def f(a: 'a'+ b, b: dict[str,int], c: x if y else z, d: (1,2), e: [1, *x], f: {1:2, **d}, g: lambda q: q, h: a.b.c, i: -x ** 2, k: f'{x!r:>{w}}', l: a or b and not c, m: x[1:2, ::3], n: ..., o: 1e10, p: 0x10) : pass\nresult = f.__annotations__",
    "local_not": FA + "def f():\n    x: undefined = 1\n    return x\nresult = f()",
    "unknown": "from __future__ import nosuch",
    "braces": "from __future__ import braces",
    "late": "x = 1\nfrom __future__ import annotations",
    "docstring": "'doc'\n" + FA + "result = 'ok'",
    "two_docstrings": "'doc'\n'doc2'\n" + FA,
    "after_future": "from __future__ import division\n" + FA + "result = 'ok'",
    "parenthesized": "from __future__ import (annotations, division,)\nresult = 'ok'",
    "as_name": "from __future__ import annotations as a\nresult = 'ok'",
    "historical": "from __future__ import absolute_import, division, generators, generator_stop, unicode_literals, print_function, nested_scopes, with_statement\nresult = 'ok'",
    "barry": "from __future__ import barry_as_FLUFL\nresult = 1 <> 2",
    "in_function": "def f():\n    from __future__ import annotations",
    "star": "from __future__ import *",
    "inherit": FA + "ns = {}\nexec('def g(x: undefined): pass', ns)\nresult = ns['g'].__annotations__",
    "dont_inherit": FA + "ns = {}\nexec(compile('def g(x: undefined): pass', '<s>', 'exec', dont_inherit=True), ns)\ntry:\n    ns['g'].__annotations__\nexcept NameError:\n    result = 'NameError'",
    "flag": "ns = {}\nexec(compile('def g(x: undefined): pass', '<s>', 'exec', flags=0x1000000), ns)\nresult = ns['g'].__annotations__",
    "after_import": "import builtins\n" + FA,
    "relative": "from .__future__ import annotations",
    "lambda_default": FA + "def f(x: int = 1 + 2): pass\nresult = (f.__annotations__, f.__defaults__)",
    "annotate": FA + "def f(x: int): pass\nresult = callable(f.__annotate__)",
    "nested_class": FA + "def outer():\n    class C:\n        x: undefined\n    return C.__annotations__\nresult = outer()",
    "generic": FA + "def f[T](x: T) -> list[T]: pass\nresult = f.__annotations__",
}


def outcome(p):
    namespace = {}
    try:
        exec(compile(SOURCES[p["case"]], "<case>", "exec", dont_inherit=True), namespace)
        return repr(namespace.get("result"))
    except Exception as error:
        return "%s: %s" % (type(error).__name__, str(error).split(" (")[0])


check_programs(outcome)
