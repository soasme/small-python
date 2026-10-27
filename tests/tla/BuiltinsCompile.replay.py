# Replays BuiltinsCompile.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
OPS = ["lookup", "store", "global_store", "delete", "function"]


def scoped(op, in_locals, in_globals, in_builtins, same):
    g = {"__builtins__": {"x": 3} if in_builtins else {}}
    if in_globals: g["x"] = 1
    l = g if same else ({"x": 2} if in_locals else {})
    source = {"lookup": "r = x", "store": "x = 5\nr = x", "global_store": "global x\nx = 5\nr = x",
              "delete": "del x\nr = 'deleted'", "function": "def f(): return x\nr = f()"}[op]
    try:
        exec(source, g, l)
        result = l["r"] if "r" in l else g["r"]
    except NameError as error:
        result = "NameError: %s" % error
    return repr((result, g.get("x"), None if same else l.get("x")))

SOURCES = {
    "eval_expression_only": "result = eval('x = 1')",
    "eval_code_object": "code = compile('1 + 2', '<s>', 'eval')\nresult = (eval(code), exec(code))",
    "exec_returns_none": "result = exec('1 + 2')",
    "eval_strips": "result = eval('  1 + 1\\n')",
    "eval_bytes": "result = eval(b'2 * 3')",
    "eval_bad_type": 'result = eval(1)',
    "eval_globals_type": "result = eval('1', [])",
    "eval_locals_mapping": "class M:\n    def __getitem__(self, k): return k * 2\n    def keys(self): return []\nresult = eval('ab', {}, M())",
    "eval_locals_keyword": "result = eval('y', locals={'y': 7})",
    "exec_closure": "def outer():\n    v = 'cell'\n    def inner(): return v\n    return inner\nf = outer()\nresult = exec(f.__code__, globals(), closure=f.__closure__)",
    "exec_closure_mismatch": 'def outer():\n    v = 1\n    def inner(): return v\n    return inner\nexec(outer().__code__, {})',
    "builtins_injected": "g = {}\nexec('pass', g)\nresult = ('__builtins__' in g, type(g['__builtins__']).__name__ in ('dict', 'module'))",
    "compile_modes": "result = [type(compile(s, '<s>', m)).__name__ for s, m in (('x', 'eval'), ('x = 1', 'exec'), ('x', 'single'))]",
    "compile_bad_mode": "result = compile('x', '<s>', 'bogus')",
    "compile_single_multi": "result = compile('x = 1\\ny = 2', '<s>', 'single')",
    "compile_eval_statement": "result = compile('x = 1', '<s>', 'eval')",
    "compile_filename": "result = compile('x', 'file.py', 'eval').co_filename",
    "compile_null": "result = compile('x\\0', '<s>', 'eval')",
    "compile_dont_inherit": "result = type(compile('x', '<s>', 'eval', dont_inherit=True)).__name__",
    "compile_bad_flags": "result = compile('x', '<s>', 'eval', flags=1 << 30)",
    "compile_optimize": "c = compile('assert False', '<s>', 'exec', optimize=1)\nexec(c)\nresult = 'skipped'",
    "compile_optimize0": "c = compile('assert False, 1', '<s>', 'exec', optimize=0)\nexec(c)",
    "compile_syntax_error": "try:\n    compile('1 +', 'f.py', 'eval')\nexcept SyntaxError as e:\n    result = (e.filename, e.lineno, type(e).__name__)",
    "single_prints_repr": "import sys\nresult = 'single'",
    "globals_is_namespace": "g = {}\nexec('r = globals() is G', g | {'G': None})\nresult = 'ok'",
    "locals_snapshot": "def f():\n    a = 1\n    l = locals()\n    a = 2\n    return (l['a'], locals()['a'])\nresult = f()",
    "locals_write_ignored": "def f():\n    a = 1\n    locals()['a'] = 5\n    return a\nresult = f()",
    "locals_module_is_globals": 'result = locals() is globals()',
    "import_builtin": "m = __import__('sys')\nresult = m.__name__",
    "import_missing": "result = __import__('nosuchmodule_xyz')",
    "import_level_bad": "result = __import__('sys', level=-1)",
    "import_empty": "result = __import__('')",
    "import_relative_no_package": "result = __import__('x', globals={}, level=1)",
    "eval_nested_scope": "x = 'module'\ndef f():\n    x = 'local'\n    return eval('x')\nresult = f()",
    "eval_free_var_missing": "def f():\n    y = 1\n    return eval('lambda: y')()\nresult = f()"
}




def generated(p):
    return scoped(p["op"], p["inl"], p["ing"], p["inb"], p["same"])


def run(p):
    if "case" not in p:
        return generated(p)
    namespace = {}
    try:
        exec(compile(SOURCES[p["case"]], "<case>", "exec"), namespace)
        return repr(namespace.get("result"))
    except SyntaxError as error:
        return "%s: %s" % (type(error).__name__, error.msg)
    except Exception as error:
        return "%s: %s" % (type(error).__name__, error)


def outcome(p):
    # TLA+ strings are ASCII.
    return run(p).encode("ascii", "backslashreplace").decode()


check_programs(outcome)
