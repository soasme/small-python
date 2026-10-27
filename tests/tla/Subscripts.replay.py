# Replays Subscripts.tla: each case gets, sets, or deletes r[FORM] for a
# logging object r (or runs one of the spec's sources), and compares the
# result and the log with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

PRE = """log = []
def t(v):
    log.append(repr(v))
    return v
class R:
    def __repr__(self):
        return 'r'
    def __getitem__(self, k):
        log.append('get %r' % (k,))
        return k
    def __setitem__(self, k, v):
        log.append('set %r %r' % (k, v))
    def __delitem__(self, k):
        log.append('del %r' % (k,))
r = R()
"""
FORMS = {"one": "1", "pair": "1, 2", "trailing": "1,", "empty": "()", "star": "*t([1, 2])", "mixed_star": "1, *t([2]), 3",
         "star_empty": "*t([])", "slice": "1:2", "slice_item": "1:2, 3", "full_slice": "::", "colon": ":",
         "step": "1:2:3", "ellipsis": "..., 1", "walrus": "a := 1", "star_slice": "*t([1]), 1:2"}
ACTIONS = {"get": "result = t(r)[%s]", "set": "t(r)[%s] = t('v')", "del": "del t(r)[%s]"}
SOURCES = {
    "aug_order": "class A:\n    def __repr__(s): return 'a'\n    def __getitem__(s, k):\n        log.append('get')\n"
                 "        return 1\n    def __setitem__(s, k, v):\n        log.append('set %r' % v)\nt(A())[t(0)] += t(5)",
    "not_subscriptable": "x = 1\nx[0]",
    "not_subscriptable_none": "x = None\nx[0]",
    "no_setitem": "class G:\n    def __getitem__(s, k): return 1\nG()[0] = 1",
    "no_delitem": "class G:\n    def __getitem__(s, k): return 1\ndel G()[0]",
    "no_delitem_key": "class G:\n    def __getitem__(s, k): return 1\ndel G()['k']",
    "tuple_assign": "(1, 2)[0] = 3",
    "str_del": "del 'a'[0]",
    "int_del": "x = 1\ndel x[0]",
    "type_del": "class P: pass\ndel P[0]",
    "type_getitem": "class G:\n    def __class_getitem__(cls, k): return ('cg', k)\nresult = G[int, str]",
    "type_not_subscriptable": "class G: pass\nG[int]",
    "list_neg": "result = ([1, 2, 3][-1], 'abc'[-3], (1, 2)[True])",
    "list_out": "[1][1]",
    "list_neg_out": "[1][-2]",
    "list_str_index": "k = 'a'\n[1][k]",
    "list_float_index": "k = 1.0\n[1][k]",
    "list_index_dunder": "class I:\n    def __index__(s): return 1\nresult = [5, 6][I()]",
    "list_big_index": "[1][2**100]",
    "tuple_out": "(1,)[5]",
    "str_out": "'a'[5]",
    "dict_missing": "{}['k']",
    "dict_tuple_key": "d = {(1, 2): 'x'}\nresult = d[1, 2]",
    "dict_unhashable": "{}[[1]]",
    "dict_missing_hook": "class D(dict):\n    def __missing__(s, k): return ('missing', k)\nresult = D()['k']",
    "range_index": "result = (range(10)[-1], range(0, 10, 3)[2], range(10)[2:5])",
    "range_out": "range(3)[3]",
    "bytes_index": "result = (b'ab'[0], bytearray(b'ab')[-1])",
    "getitem_none": "class G:\n    __getitem__ = None\nG()[0]",
    "list_set_out": "l = [1]\nl[5] = 1",
    "list_del_out": "l = [1]\ndel l[5]",
    "seq_getitem_iter": "class S:\n    def __getitem__(s, i):\n        if i > 2: raise IndexError\n        return i\nresult = list(S())",
    "generator_subscript": "r[x for x in [1]]",
    "star_in_slice": "r[*a:b]",
    "star_bare_index": "r[*]",
    "nested_star": "result = r[*t((1,)), *t((2,))]",
}


def outcome(p):
    source = SOURCES[p["case"]] if "case" in p else ACTIONS[p["action"]] % FORMS[p["form"]]
    namespace = {}
    try:
        exec(compile(PRE + source, "<subscript>", "exec"), namespace)
        result = repr(namespace.get("result"))
    except Exception as error:
        result = "%s: %s" % (type(error).__name__, str(error).split(" (")[0])
    return (result, tuple(namespace.get("log", ())))


check_programs(outcome)
