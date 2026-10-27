# Replays Comparisons.tla: each case builds the spec's classes A and B and
# compares their instances (or runs one of the spec's sources), logging the
# comparison methods called and the operands evaluated, and compares the
# result and the log with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

METHODS = ("__eq__", "__ne__", "__lt__", "__le__", "__gt__", "__ge__")
PRE = "log = []\ndef t(v):\n    log.append(v)\n    return v\n"
SOURCES = {
    "chain_once": "result = t(1) < t(2) < t(3)",
    "chain_short": "result = t(3) < t(2) < t(1)",
    "chain_mixed": "result = 1 < 2 == 2 > 0 != 5 in [5] is not None",
    "chain_value": "class V:\n    def __lt__(s, o): return 'v'\nresult = V() < 1 < 2",
    "chain_value_false": "class V:\n    def __lt__(s, o): return ''\nresult = V() < t(1) < t(2)",
    "is_ident": "a = [1]\nb = [1]\nresult = (a is a, a is b, a is not b, a == b)",
    "is_none": "result = (None is None, type(None)() is None)",
    "nan": "n = float('nan')\nresult = (n == n, n != n, n < n, [n] == [n], n in [n], (n,) == (n,))",
    "nan_distinct": "result = [float('nan')] == [float('nan')]",
    "seq_lex": "result = ([1, 2] < [1, 3], [1, 2] < [1, 2, 0], (1, 2) == (1, 2.0), [1] == (1,), 'ab' < 'b', b'a' < b'b')",
    "seq_type_err": "[1] < (1,)",
    "seq_elem_err": "[1, 'a'] < [1, 2]",
    "str_int_eq": "result = ('1' == 1, '1' != 1)",
    "order_err": "1 < 'a'",
    "order_err_none": "None < None",
    "dict_eq": "result = ({1: 2, 3: 4} == {3: 4, 1: 2}, {1: 2} == {1: 3})",
    "dict_order": "{} < {}",
    "set_order": "result = ({1} < {1, 2}, {1, 2} <= {1, 2}, {1} < {2}, {1} > {2}, {1} == frozenset({1}))",
    "range_eq": "result = (range(0) == range(2, 2), range(0, 3, 2) == range(0, 4, 2), range(1) == [0])",
    "int_float": "result = (1 == 1.0, 2**53 + 1 == float(2**53 + 1), 2**53 + 1 > float(2**53), 10**400 > 1e308, -0.0 == 0)",
    "complex_order": "1j < 2j",
    "complex_eq": "result = (1 + 0j == 1, 1j == 1j)",
    "bool_int": "result = (True == 1, False < True, True + True)",
    "in_list": "result = (2 in [1, 2], 3 not in [1, 2], 'b' in 'abc', 'bc' in 'abc', '' in 'a', 1 in {1: 2}, 2 in {1: 2})",
    "in_str_type": "1 in 'abc'",
    "in_bytes_type": "'a' in b'a'",
    "in_identity": "class E:\n    def __eq__(s, o): return False\ne = E()\nresult = (e in [e], e == e)",
    "contains_nonbool": "class C:\n    def __contains__(s, x): return t('yes')\nresult = (1 in C(), 1 not in C())",
    "contains_falsy": "class C:\n    def __contains__(s, x): return 0\nresult = 1 in C()",
    "contains_iter": "class C:\n    def __iter__(s):\n        yield t(1)\n        yield t(2)\n        yield t(3)\nresult = 2 in C()",
    "contains_getitem": "class C:\n    def __getitem__(s, i):\n        if i > 3: raise IndexError\n        return t(i * 10)\nresult = (20 in C(), 50 in C())",
    "contains_none": "class C: pass\n1 in C()",
    "contains_is_none": "class C:\n    __contains__ = None\n    def __iter__(s): return iter([1])\n1 in C()",
    "contains_raises": "class C:\n    def __contains__(s, x): raise KeyError('k')\n1 in C()",
    "in_dict_unhashable": "[] in {}",
    "in_set_unhashable": "result = [] in set()",
    "in_set_of_set": "result = {1} in {frozenset({1})}",
    "not_in_precedence": "result = not 1 in [1]",
    "eq_returns_value": "class V:\n    def __eq__(s, o): return 'x'\nresult = (V() == 1, V() != 1, 1 == V())",
    "hash_none_eq": "class V:\n    def __eq__(s, o): return True\nresult = V.__hash__",
    "list_identity_shortcut": "class E:\n    def __eq__(s, o): return t('eq')\ne = E()\nresult = ([e] == [e], [e] == [E()])",
}


def build(kind, name, base, log):
    def method(m):
        def compare(self, other):
            entry = "%s.%s(%s)" % (name, m, self.side)
            log.append(entry)
            return NotImplemented if kind == "notimpl" else entry
        return compare

    names = METHODS if kind in ("value", "notimpl") else ("__eq__",) if kind == "eq_only" else ()
    return type(name, (base,), {m: method(m) for m in names})


def outcome(p):
    namespace = {}
    if "case" in p:
        try:
            exec(compile(PRE + SOURCES[p["case"]], "<case>", "exec"), namespace)
            result = repr(namespace.get("result"))
        except Exception as error:
            result = "%s: %s" % (type(error).__name__, str(error).split(" (")[0])
        return (result, tuple(map(repr, namespace.get("log", ()))))
    log = []
    A = build(p["left"], "A", object, log)
    B = build(p["right"], "B", A if p["relation"] == "sub" else object, log)
    a, b = A(), B()
    a.side, b.side = "L", "R"
    try:
        result = repr(eval("a %s b" % p["op"], {"a": a, "b": b}))
    except TypeError as error:
        result = "TypeError: %s" % error
    return (result, tuple(log))


check_programs(outcome)
