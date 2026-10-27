# Replays Grammar.tla: a suite program runs its compound statement after a
# prelude defining the logging helpers and compares the log; a snippet is
# only compiled. Exceptions are compared by type and message.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

HEADERS = {"if_true": "if yes:", "if_false": "if no:", "while": "while go():", "for": "for _ in [0]:",
           "with": "with Ctx():", "try": "try:", "def": "def f():", "class": "class K:"}
AFTER = {"try": "finally: a(9)", "def": "f()"}
FORMS = {"inline1": " a(1)", "inline2": " a(1); a(2)", "trailing": " a(1);", "block": "\n    a(1)",
         "block2": "\n    a(1)\n    a(2)", "nested": " if yes: a(1)", "missing": "\na(1)", "block_semis": "\n    a(1); a(2)",
         "dedent_mismatch": "\n    a(1)\n  a(2)", "block_then_inline": "\n    a(1)\n    if yes: a(2)"}
PRE = """log = []
def a(x): log.append(x)
yes, no = True, False
state = [True]
def go():
    r = state[0]; state[0] = False; return r
class Ctx:
    def __enter__(self): log.append('enter')
    def __exit__(self, *e): log.append('exit')
"""
def source(kind, form):
    s = HEADERS[kind] + FORMS[form]
    if kind in AFTER: s += "\n" + AFTER[kind]
    return s + "\n"


SNIPPETS = {
    "soft_keywords_as_names": "match = 1\ncase = 2\ntype = 3\n_ = 4\nlazy = 5\nprint(match, case, type, _, lazy)",
    "match_soft": "match x:\n    case [1, *rest] if rest:\n        pass\n    case {'k': v, **kw}:\n        pass\n    case Point(x=0) | None:\n        pass\n    case _:\n        pass",
    "return_star": "def f():\n    return *a, *b",
    "assign_star_tuple": "x = *a,",
    "assign_star_alone": "x = *a",
    "del_targets": "del (a), [b], c.d, e[0]",
    "call_dstar_then_star": "f(**a, *b)",
    "call_kw_then_pos": "f(a=1, b)",
    "call_genexpr_unparenthesized": "f(x for x in y, 1)",
    "call_keyword_repeated": "f(a=1, a=2)",
    "decorator_expression": "@a[0].b(1)\ndef f(): pass",
    "lambda_bare_star": "lambda *: 0",
    "lambda_kwonly": "lambda *, k: k",
    "def_slash_first": "def f(/, a): pass",
    "def_params_full": "def f(a, b=1, /, c=2, *d, e, f=3, **g): pass",
    "def_duplicate_param": "def f(a, a): pass",
    "def_default_order": "def f(a=1, b): pass",
    "slice_tuple": "a[1:2, ::3, ...]",
    "subscript_star": "a[*b]",
    "with_parenthesized": "with (a as b, c as d,):\n    pass",
    "except_star": "try:\n    pass\nexcept* E:\n    pass",
    "except_mixed": "try:\n    pass\nexcept* E:\n    pass\nexcept F:\n    pass",
    "except_unparenthesized": "try:\n    pass\nexcept E, F:\n    pass",
    "except_unparenthesized_as": "try:\n    pass\nexcept E, F as e:\n    pass",
    "try_alone": "try:\n    pass\nx = 1",
    "walrus_if": "if (n := 10) > 5:\n    pass",
    "walrus_unparenthesized_stmt": "n := 10",
    "unpack_targets": "(a, b), [c, *d], e.f, g[0] = h",
    "two_starred_targets": "*a, *b = c",
    "fstring_debug": "f'{x=!r:>10}'",
    "tstring": "t'{x}'",
    "type_stmt": "type X[T] = list[T]",
    "class_type_params": "class A[T: int, *Ts, **P]:\n    pass",
    "annotated_single": "(x): int = 1",
    "annotated_tuple": "x, y: int",
    "assign_literal": "1 = x",
    "assign_call": "f() = 1",
    "conditional_without_else": "x = 1 if y",
    "print_statement": "print 'x'",
    "missing_comma": "a b",
    "else_alone": "else:\n    pass",
    "return_outside": "return 1",
    "break_outside": "break",
    "continue_outside": "continue",
    "await_outside": "await x",
    "yield_outside": "yield 1",
    "nonlocal_module": "nonlocal x",
    "global_after_use": "def f():\n    x = 1\n    global x",
    "chained_conditional": "a if b else c if d else e",
    "comprehension_ifs": "[x for x in y if a if b]",
    "dict_unpack_display": "{**a, 'b': 1, **c}",
    "async_constructs": "async def f():\n    async with a as b:\n        async for c in d:\n            await e\n    return [x async for x in y]",
    "yield_from_expr": "def g():\n    x = yield from y",
    "lazy_import": "lazy import a.b\nlazy from c import d",
    "lazy_in_function": "def f():\n    lazy import a",
    "lazy_star": "lazy from a import *",
    "star_in_index_assign": "a[*b] = c",
    "keyword_as_identifier": "class = 1",
    "dotted_import_as": "import a.b as c, d",
    "relative_import_star": "from .. import *",
    "import_star_function": "def f():\n    from a import *",
    "pass_semicolons": "pass; pass;",
    "double_semicolon": "pass;; pass",
    "backslash_continuation": "x = 1 + \\\n    2",
    "implicit_continuation": "x = (1 +\n 2)",
    "decorated_class": "@d\nclass A: pass",
    "async_lambda": "async lambda: 0",
    "star_expression_for": "for x in *a, *b:\n    pass",
    "assert_message": "assert x, 'm'",
    "raise_from": "raise E from None",
    "default_after_star": "def f(*, a=1, b): pass",
    "kwargs_then_param": "def f(**k, a): pass"
}


def outcome(p):
    try:
        if "snippet" in p:
            compile(SNIPPETS[p["snippet"]] + "\n", "<case>", "exec")
            return "'compiled'"
        namespace = {}
        exec(PRE, namespace)
        exec(compile(source(p["kind"], p["form"]), "<case>", "exec"), namespace)
        return repr(namespace["log"])
    except SyntaxError as error:
        return "%s: %s" % (type(error).__name__, error.msg)


check_programs(outcome)
