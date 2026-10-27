# Replays Conditionals.tla: each case runs the spec's if statement or
# while loop with logging conditions and suites (or one of the spec's
# sources), and compares the result and the log with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

PRE = "log = []\ndef t(v):\n    log.append(repr(v))\n    return v\n"
SOURCES = {
    "break_outside": "break",
    "continue_outside": "continue",
    "break_in_function_in_loop": "while True:\n    def f():\n        break",
    "continue_in_finally": "i = 0\nwhile i < 2:\n    i += 1\n    try:\n        pass\n    finally:\n        continue\nresult = i",
    "break_in_finally": "while True:\n    try:\n        1/0\n    finally:\n        break\nresult = 'swallowed'",
    "nested_break": "out = []\nfor i in range(2):\n    while True:\n        out.append(i)\n        break\nresult = out",
    "elif_after_else": "if 1:\n    pass\nelse:\n    pass\nelif 2:\n    pass",
    "if_walrus": "if (n := 5) > 3:\n    result = n",
    "while_walrus": "data = [1, 2, 0, 3]\nout = []\nwhile (x := data.pop(0)):\n    out.append(x)\nresult = out",
    "if_bool_error": "class B:\n    def __bool__(self): raise ValueError('no')\nif B():\n    pass",
    "while_cond_each_time": "calls = []\ndef c():\n    calls.append(1)\n    return len(calls) < 3\nwhile c():\n    pass\nresult = len(calls)",
    "if_empty_body": "if 1:\npass",
    "while_else_after_break_in_nested": "for i in range(1):\n    while False:\n        pass\n    else:\n        result = 'else ran'",
    "if_expression_value": "result = [('a' if x else 'b') for x in (0, 1)]",
    "conditional_expr_lazy": "seen = []\nresult = (seen.append('t') or 1) if 0 else (seen.append('f') or 2)\nresult = (result, seen)",
    "conditional_expr_precedence": "result = 1 if 0 else 2 if 0 else 3",
    "conditional_expr_lambda": "f = lambda: 1 if 0 else 2\nresult = f()",
}


def source(p):
    if "conditions" in p:
        lines = []
        for k, condition in enumerate(p["conditions"], 1):
            lines += ["%s t(%s):" % ("if" if k == 1 else "elif", condition), "    log.append('branch %d')" % k]
        if p["else"]:
            lines += ["else:", "    log.append('else')"]
        return "\n".join(lines)
    if "n" in p:
        lines = ["i = 0", "while t(i < %d):" % p["n"], "    i += 1",
                 "    if i == %d:" % p["break"], "        log.append('break')", "        break",
                 "    if i == %d:" % p["continue"], "        log.append('continue')", "        continue",
                 "    log.append('body %d' % i)"]
        if p["else"]:
            lines += ["else:", "    log.append('else')"]
        return "\n".join(lines)
    return SOURCES[p["case"]]


def outcome(p):
    namespace = {}
    try:
        exec(compile(PRE + source(p), "<statement>", "exec"), namespace)
        result = repr(namespace.get("result"))
    except SyntaxError as error:
        result = "%s: %s" % (type(error).__name__, error.msg)
    except Exception as error:
        result = "%s: %s" % (type(error).__name__, error)
    return (result, tuple(namespace.get("log", ())))


check_programs(outcome)
