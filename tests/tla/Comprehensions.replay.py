# Replays Comprehensions.tla: each case builds the spec's comprehension (or
# runs one of the spec's sources), logging iterables, tested sums, and
# elements as they are evaluated, and compares the result and the log with
# the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

PRE = "log = []\ndef t(v):\n    log.append(v)\n    return v\n"
SOURCES = {
    "no_leak": "x = 'outer'\n[x for x in range(3)]\nresult = x",
    "class_scope": "class C:\n    a = 1\n    b = [a for _ in range(2)]\nresult = C.b",
    "class_scope_inner": "class C:\n    a = [1]\n    try:\n        b = [y for x in a for y in a]\n"
                         "    except NameError as e:\n        b = str(e)\nresult = C.b",
    "class_first_iterable": "class C:\n    a = [1, 2]\n    b = [x for x in a]\nresult = C.b",
    "walrus_binds": "result = ([y := x for x in range(3)], y)",
    "walrus_iter_var": "[x := 1 for x in range(3)]",
    "walrus_iterable": "[x for x in (y := [1])]",
    "walrus_class": "class C:\n    [y := 1 for x in range(1)]",
    "yield_in": "def f():\n    [(yield x) for x in range(3)]",
    "await_outside": "[await x for x in y]",
    "async_for_outside": "def f():\n    return [x async for x in y]",
    "gen_sole_arg": "result = sum(t(x) for x in range(3))",
    "gen_not_sole": "sum(x for x in range(3), 1)",
    "gen_first_error": "g = (x for x in 1)",
    "gen_inner_error": "g = (y for x in [1] for y in x)\nt('created')\nlist(g)",
    "comp_error_type": "[x for x in 5]",
    "star_list": "result = [*t(x) for x in [[1, 2], [3]]]",
    "dstar_dict": "result = {**t(d) for d in [{1: 2}, {3: 4, 1: 5}]}",
    "star_gen": "result = list(*x for x in [[1], [2, 3]])",
    "dstar_list": "[**d for d in ds]",
    "star_dict_key": "{*x: 1 for x in y}",
    "star_dict_bad": "{*x for x in [1]}",
    "dstar_bad": "{**x for x in [1]}",
    "star_target_in_comp": "result = [b for a, *b in [(1, 2, 3)]]",
    "nested_scope": "def f():\n    n = 10\n    return [x + n for x in range(2)]\nresult = f()",
    "late_binding": "fs = [lambda: x for x in range(3)]\nresult = [f() for f in fs]",
    "gen_close": "g = (t(x) for x in range(5))\nnext(g)\ng.close()\nresult = list(g)",
    "gen_send_none": "g = (x for x in range(2))\nresult = (g.send(None), next(g))",
    "gen_name": "g = (x for x in [])\nresult = (g.__name__, g.__qualname__)",
    "frame_name": "import sys\nresult = [sys._getframe().f_code.co_name for _ in [1]]",
    "unparenthesized_tuple": "[x, y for x in a]",
    "if_else_elem": "result = [x if x % 2 else -x for x in range(4)]",
    "if_without_else": "[x for x in a if x else 1]",
    "lambda_in_if": "result = [x for x in range(4) if (lambda: x % 2)()]",
    "iter_var_global": "def f():\n    global x\n    return [x for x in range(2)]\nx = 'g'\nresult = (f(), x)",
}


def comprehension(p):
    kind, clauses = p["kind"], p["clauses"]
    parts, bound = [], []
    for k, clause in enumerate(clauses, 1):
        if clause == "for":
            step = 10 ** (k - 1)
            parts.append(f"for x{k} in t([{step}, {2 * step}])")
            bound.append(f"x{k}")
        else:
            parts.append(f"if t({' + '.join(bound)}) % 2")
    s = "(" + " + ".join(bound) + ")"
    if kind == "dict":
        element = f"t({s}): t(-{s})" if p["element"] == "plain" else f"**t({{{s}: -{s}}})"
    else:
        element = f"t({s})" if p["element"] == "plain" else f"*t(({s}, -{s}))"
    body = element + " " + " ".join(parts)
    if kind == "gen":
        return f"g = ({body})\nt('created')\nresult = list(g)"
    return "result = " + ("[%s]" if kind == "list" else "{%s}") % body + "\nt('created')"


def outcome(p):
    namespace = {}
    source = SOURCES[p["case"]] if "case" in p else comprehension(p)
    try:
        exec(compile(PRE + source, "<comprehension>", "exec"), namespace)
    except Exception as error:
        return ("%s: %s" % (type(error).__name__, str(error).split(" (")[0]), (), tuple(map(repr, namespace.get("log", ()))))
    result, log = namespace.get("result"), tuple(map(repr, namespace["log"]))
    if "case" in p:
        return ("ok", repr(result), log)
    if type(result) is set:
        value = frozenset(repr(x) for x in result)
    elif type(result) is dict:
        value = tuple((repr(k), repr(v)) for k, v in result.items())
    else:
        value = tuple(repr(x) for x in result)
    return ("ok", value, log)


check_programs(outcome)
