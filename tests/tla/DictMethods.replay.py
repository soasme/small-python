# Replays DictMethods.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
class Missing(dict):
    def __missing__(self, key): return key * 2
class KeysOnly:
    def keys(self): return ['a', 'b']
    def __getitem__(self, k): return k.upper()
KEYS = [1, 2, 3]
VALS = [10, 20]
MAPS = [()] + [((k, v),) for k in KEYS for v in VALS] + [((k1, v1), (k2, v2)) for k1 in KEYS for k2 in KEYS if k1 != k2 for v1 in VALS for v2 in VALS]
OPS = ["merge", "update", "ior", "equal", "keys_and", "keys_or", "keys_sub", "keys_xor", "items_and", "items_sub", "keys_le", "keys_disjoint", "values_list", "reversed_items"]


def dict_op(op, a, b):
    d1, d2 = dict(a), dict(b)
    if op == "merge": return repr(d1 | d2)
    if op == "update": d1.update(d2); return repr(d1)
    if op == "ior": d = d1; d1 |= d2; return repr((d1, d is d1))
    if op == "equal": return repr(d1 == d2)
    if op == "keys_and": return repr(sorted(d1.keys() & d2.keys()))
    if op == "keys_or": return repr(sorted(d1.keys() | d2.keys()))
    if op == "keys_sub": return repr(sorted(d1.keys() - d2.keys()))
    if op == "keys_xor": return repr(sorted(d1.keys() ^ d2.keys()))
    if op == "items_and": return repr(sorted(d1.items() & d2.items()))
    if op == "items_sub": return repr(sorted(d1.items() - d2.items()))
    if op == "keys_le": return repr(d1.keys() <= d2.keys())
    if op == "keys_disjoint": return repr(d1.keys().isdisjoint(d2.keys()))
    if op == "values_list": v = d1.values(); d1.update(d2); return repr(list(v))
    if op == "reversed_items": k = d1.items(); d1.update(d2); return repr(list(reversed(k)))



SOURCES = {
    "ctor_forms": "result = [dict(one=1, two=2), dict({'one': 1, 'two': 2}), dict(zip(['one', 'two'], [1, 2])), dict([('two', 2), ('one', 1)]), dict({'one': 1}, two=2), dict(KeysOnly())]",
    "ctor_equal": "a = dict(one=1, two=2, three=3)\nb = {'one': 1, 'two': 2, 'three': 3}\nc = dict(zip(['one', 'two', 'three'], [1, 2, 3]))\nd = dict([('two', 2), ('one', 1), ('three', 3)])\ne = dict({'three': 3, 'one': 1, 'two': 2})\nf = dict({'one': 1, 'three': 3}, two=2)\nresult = a == b == c == d == e == f",
    "ctor_bad_item": 'result = dict([(1, 2, 3)])',
    "ctor_bad_element": 'result = dict([1])',
    "ctor_two_positional": 'result = dict({}, {})',
    "fromkeys": "result = (dict.fromkeys('ab'), dict.fromkeys([1, 2], 0), type(Missing.fromkeys('a')).__name__)",
    "fromkeys_shared": "d = dict.fromkeys('ab', [])\nd['a'].append(1)\nresult = d",
    "missing_hook": "d = Missing(a=1)\nresult = (d['a'], d['zz' * 1], 'zz' in d, d.get('q'))",
    "keyerror": "result = {}['k']",
    "keyerror_tuple": 'result = {}[(1,)]',
    "unhashable_key": 'result = {[]: 1}',
    "get_default": "result = ({}.get(1), {}.get(1, 'd'), {1: 0}.get(1, 'd'))",
    "pop_default": "d = {1: 2}\nresult = (d.pop(1), d.pop(1, 'd'), d)",
    "pop_missing": 'result = {}.pop(1)',
    "popitem_lifo": 'd = {1: 1, 2: 2, 3: 3}\nresult = (d.popitem(), d.popitem(), d)',
    "popitem_empty": 'result = {}.popitem()',
    "setdefault": "d = {}\nresult = (d.setdefault('a'), d.setdefault('b', 1), d.setdefault('b', 2), d)",
    "update_forms": "d = {}\nd.update({'a': 1}, b=2)\nd.update([('c', 3)])\nd.update(KeysOnly())\nresult = d",
    "update_bad": 'result = {}.update(1)',
    "update_too_many": 'result = {}.update({}, {})',
    "or_non_dict": 'result = {} | [1]',
    "ior_iterable": "d = {}\nd |= [('a', 1)]\nresult = d",
    "copy_shallow": "a = {'k': []}\nb = a.copy()\nb['k'].append(1)\nb['n'] = 1\nresult = (a, b)",
    "clear": 'd = {1: 2}\ne = d\nd.clear()\nresult = e',
    "len_iter_reversed": "d = {'one': 1, 'two': 2, 'three': 3, 'four': 4}\nresult = (len(d), list(d), list(reversed(d)), list(reversed(d.values())))",
    "order_reinsert": "d = {'one': 1, 'two': 2}\nd['one'] = 42\ndel d['two']\nd['two'] = None\nresult = d",
    "equality_ignores_order": 'result = ({1: 1, 2: 2} == {2: 2, 1: 1}, list({1: 1, 2: 2}) == list({2: 2, 1: 1}))',
    "no_ordering": 'result = {} < {}',
    "unhashable_dict": 'result = hash({})',
    "view_live": "d = {'a': 1}\nk, v, i = d.keys(), d.values(), d.items()\nd['b'] = 2\nresult = (list(k), list(v), list(i), len(k))",
    "view_mapping": "d = {'a': 1}\nresult = (d.keys().mapping == d, type(d.keys().mapping).__name__, d.items().mapping['a'])",
    "view_contains": "d = {'a': 1}\nresult = ('a' in d.keys(), 1 in d.values(), ('a', 1) in d.items(), ('a', 2) in d.items())",
    "view_set_ops_iterable": "d = {'a': 1, 'b': 2}\nresult = (sorted(d.keys() & ['a', 'x']), sorted(d.keys() | 'xy'), sorted(d.keys() - {'a'}), sorted(['b', 'z'] & d.keys()))",
    "view_set_ops_return_set": 'result = type({1: 1}.keys() & {1}).__name__',
    "values_no_set_ops": 'result = {1: 1}.values() & {1}',
    "values_equality": 'd = {1: 1}\nresult = (d.values() == d.values(), d.keys() == {1}, d.items() == {(1, 1)})',
    "items_unhashable_value": 'd = {1: []}\nresult = (1, []) in d.items()',
    "items_set_op_unhashable": 'd = {1: []}\nresult = d.items() & {(1, 2)}',
    "view_changed_size": 'd = {1: 1}\nfor k in d.keys(): d[k + 1] = 1',
    "view_reversed_type": 'result = type(reversed({}.keys())).__name__',
    "view_repr": "d = {'a': 1}\nresult = (repr(d.keys()), repr(d.values()), repr(d.items()))",
    "view_hash": 'result = hash({}.keys())',
    "view_comparisons": 'd = {1: 1, 2: 2}\nresult = ({1}.issubset(d.keys()), d.keys() >= {1}, d.keys() < {1, 2, 3}, d.keys() > d.keys())',
    "view_isdisjoint": 'result = ({1: 1}.keys().isdisjoint([2]), {1: 1}.items().isdisjoint([(1, 1)]))',
    "repr_recursive": "d = {}\nd['self'] = d\nresult = repr(d)",
    "iter_type_names": 'd = {1: 1}\nresult = [type(iter(x)).__name__ for x in (d, d.keys(), d.values(), d.items())]',
    "dict_subclass_or": 'result = type(Missing() | {}).__name__',
    "keys_order_after_pop": "d = dict.fromkeys('abc')\nd.pop('a')\nd['a'] = 1\nresult = list(d)",
    "float_int_key": "d = {1: 'int'}\nd[1.0] = 'float'\nd[True] = 'bool'\nresult = (d, type(list(d)[0]).__name__)",
    "nan_key": "n = float('nan')\nd = {n: 1}\nresult = (d[n], float('nan') in d)"
}


TYPES = {name: value for name, value in list(globals().items()) if isinstance(value, type) and name[0].isupper()}

def generated(p):
    return dict_op(p["op"], p["a"], p["b"])


def run(p):
    if "case" not in p:
        return generated(p)
    namespace = dict(TYPES)
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
