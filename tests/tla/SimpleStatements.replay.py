# Replays SimpleStatements.tla: each case assigns to, augments, or deletes
# the spec's targets on logging objects o and r (or runs one of the spec's
# sources), and compares the result and the log with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

PRE = """log = []
def t(v):
    log.append(repr(v))
    return v
class O:
    def __repr__(self): return 'o'
    def __setattr__(self, n, v):
        log.append('setattr %s %r' % (n, v))
    def __getattr__(self, n):
        log.append('getattr %s' % n)
        return 10
    def __delattr__(self, n):
        log.append('delattr %s' % n)
class R:
    def __repr__(self): return 'r'
    def __getitem__(self, k):
        log.append('get %r' % (k,))
        return 10
    def __setitem__(self, k, v):
        log.append('set %r %r' % (k, v))
    def __delitem__(self, k):
        log.append('del %r' % (k,))
o = O()
r = R()
"""

SOURCES = {
    "chain_names": "a = b = t([])\nresult = a is b",
    "swap": "a, b = 1, 2\na, b = b, a\nresult = (a, b)",
    "swap_index": "l = [0, 1]\ni = 0\ni, l[i] = 1, 9\nresult = l",
    "star_target": "a, *b, c = t(range(5))\nresult = (a, b, c)",
    "star_only": "*a, = 'xy'\nresult = a",
    "star_alone": "*a = [1]",
    "two_stars": "*a, *b = [1]",
    "nested_target": "(a, [b, c]) = (1, (2, 3))\nresult = (a, b, c)",
    "list_target": "[a, b] = 'xy'\nresult = (a, b)",
    "slice_assign": "l = [1, 2, 3, 4]\nl[1:3] = 'ab'\nresult = l",
    "ext_slice_len": "l = [1, 2, 3, 4]\nl[::2] = [9]",
    "too_many": "a, b = [1, 2, 3]",
    "too_few": "a, b, c = [1, 2]",
    "star_too_few": "a, *b, c = [1]",
    "not_iterable": "a, b = 1",
    "assign_literal": "1 = a",
    "assign_call": "f() = 1",
    "assign_keyword": "None = 1",
    "assign_debug": "__debug__ = 1",
    "aug_name_unbound": "def f():\n    x += 1\nf()",
    "aug_tuple": "a, b += 1",
    "aug_star": "*a += 1",
    "aug_list_identity": "l = [1]\nm = l\nl += [2]\nresult = (m, m is l)",
    "aug_tuple_identity": "t1 = (1,)\nt2 = t1\nt1 += (2,)\nresult = (t2, t1 is t2)",
    "aug_tuple_item_list": "tp = ([1],)\ntry:\n    tp[0] += [2]\nexcept TypeError as e:\n    result = (tp, str(e))",
    "ann_assign_order": "t(o).z: t(int) = t(5)",
    "ann_no_value_attr": "t(o).z: t(int)",
    "ann_tuple": "a, b: int = 1, 2",
    "assert_true": "assert t(1), t('msg')\nresult = 'ok'",
    "assert_false": "assert t(0), t('msg')",
    "assert_no_msg": "assert t([])",
    "assert_exc_class": "try:\n    assert False, 'm'\nexcept AssertionError as e:\n    result = (type(e).__name__, e.args)",
    "assert_debug": "result = __debug__",
    "del_name": "a = 1\ndel a\na",
    "del_unbound": "def f():\n    del x\nf()",
    "del_global_missing": "del nosuchname",
    "del_nested": "a, b = 1, 2\ndel (a, [b])\nresult = 'a' in dir() or 'b' in dir()",
    "del_slice": "l = [1, 2, 3, 4]\ndel l[::2]\nresult = l",
    "del_star": "del *a",
    "del_literal": "del 1",
    "del_call": "del f()",
    "del_local_then_use": "def f():\n    x = 1\n    del x\n    return x\nf()",
    "del_free_var": "def f():\n    x = 1\n    def g(): return x\n    del x\n    return g()\nf()",
    "del_attr_missing": "class P: pass\ndel P().nope",
    "pass_stmt": "pass\nresult = 'ok'",
}


def target(kind, i, list_number=1):
    return {"name": "n%d%d" % (list_number, i), "attr": "t(o).a%d" % i, "item": "t(r)[t(%d)]" % i}[kind]


def source(p):
    if "assign" in p:
        targets = p["assign"]
        value = "t('v')" if len(targets) == 1 else "t((1, 2))"
        lists = [", ".join(target(k, i, j) for i, k in enumerate(targets, 1)) for j in range(1, p["chain"] + 1)]
        return " = ".join(lists) + " = " + value
    if "augment" in p:
        return {"name": "n = 10\nn += t(1)\nresult = n", "attr": "t(o).x += t(1)", "item": "t(r)[t(1)] += t(1)"}[p["augment"]]
    if "delete" in p:
        names = [target(k, i) for i, k in enumerate(p["delete"], 1) if k == "name"]
        return "".join(n + " = 1\n" for n in names) + "del " + ", ".join(target(k, i) for i, k in enumerate(p["delete"], 1))
    return SOURCES[p["case"]]


def outcome(p):
    namespace = {}
    try:
        exec(compile(PRE + source(p), "<statement>", "exec"), namespace)
        result = repr(namespace.get("result"))
    except SyntaxError as error:
        result = "SyntaxError: %s" % error.msg
    except Exception as error:
        result = "%s: %s" % (type(error).__name__, error)
    return (result, tuple(namespace.get("log", ())))


check_programs(outcome)
