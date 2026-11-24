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
class H:
    log = []
    def __init__(self, v): self.v = v
    def __hash__(self):
        for _ in range(2): pass
        H.log.append(self.v); return self.v
    def __eq__(self, other): return isinstance(other, H) and other.v == self.v
class Unhashed:
    def __hash__(self):
        for _ in range(2): pass
        raise TypeError('no')
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
    "ctor_iter_pairs": "class P:\n    def __init__(s, items): s.items = items\n    def __iter__(s):\n        for _ in (): pass\n"
                       "        return iter(s.items)\nd = {'x': 0}\nd.update(P([('x', 1), 'yz']))\n"
                       "result = [dict(P([('a', 1), ['b', 2], ('a', 3)])), d]",
    "ctor_iter_bad_pair": "class P:\n    def __iter__(s):\n        for _ in (): pass\n        return iter([('a', 1), (1, 2, 3)])\n"
                          "result = dict(P())",
    "ctor_listed_pairs": "def g(k, v):\n    for _ in (): pass\n    yield k\n    yield v\n"
                         "def bad():\n    yield 1\n    raise TypeError('t')\n"
                         "d = {'x': 0}\nd.update([g('y', 3)])\ntry: dict([('a', 1), bad()])\nexcept TypeError as e: notes = e.__notes__\n"
                         "result = [dict([g('a', 1), g('b', 2)]), d, notes]",
    "ctor_iter_keywords": "class P:\n    def __iter__(s):\n        for _ in (): pass\n        return iter([('a', 1), ('b', 2)])\n"
                          "d = {}\nd.update(P(), b=3, **{'c': 4})\nresult = [dict(P(), a=0), d]",
    "ctor_iter_keywords_fails": "class G:\n    def __iter__(s):\n        for _ in (): pass\n        yield 'a', 1\n        raise LookupError('g')\n"
                                "d = {}\ntry: d.update(G(), z=1)\nexcept LookupError: pass\nresult = d",
    "ctor_two_positional": 'result = dict({}, {})',
    "get_keyed_eq": ("log = []\nclass K(str):\n    def __eq__(s, o):\n        log.append(o); return str.__eq__(s, o)\n"
                     "    __hash__ = str.__hash__\nd = {'a': 1, K('k'): 2}\n"
                     "result = (d.get('k'), d.setdefault('k', 0), list(map(d.get, ['k', 'a'])), d.pop('k'), log)"),
    "update_unbound": ("log = []\nclass M:\n    def keys(s):\n        for _ in (): pass\n        log.append('k'); return [1]\n"
                       "    def __getitem__(s, k): log.append(k); return 2\n"
                       "class S(dict):\n    def __setitem__(s, k, v): log.append('set'); dict.__setitem__(s, k, v)\n"
                       "s = S(); d = {}; l = []\ndict.update(d, M(), z=0); s.update(M()); dict.update(s, iter([(3, 4)]))\n"
                       "list(map(l.extend, [iter([5])]))\nresult = (d, dict(s), l, log)"),
    "fromkeys_class": ("log = []\nclass S(dict):\n    def __init__(s):\n        for _ in (): pass\n        log.append('n')\n"
                       "    def __setitem__(s, k, v):\n        log.append(k); dict.__setitem__(s, k, v)\n"
                       "def g():\n    yield 1\n    log.append('y'); yield 2\n    log.append('y'); yield 3\n"
                       "class F(frozendict): pass\nd = S.fromkeys(g(), 0)\nf = F.fromkeys(iter([1, 2]))\n"
                       "result = (log, dict(d), type(f).__name__, dict(f))"),
    "fromkeys_iter_source": ("log = []\nclass I:\n    def __iter__(s):\n        for _ in (): pass\n        log.append('i'); return iter([4])\n"
                             "class S(dict): pass\nclass F(frozendict): pass\n"
                             "result = (S.fromkeys(I()), F.fromkeys(I(), 1), dict.fromkeys(I()), log)"),
    "fromkeys": "result = (dict.fromkeys('ab'), dict.fromkeys([1, 2], 0), type(Missing.fromkeys('a')).__name__)",
    "fromkeys_shared": "d = dict.fromkeys('ab', [])\nd['a'].append(1)\nresult = d",
    "fromkeys_hashed": "H.log.clear()\nd = dict.fromkeys([H(1), 2, H(3), H(1)], 0)\nresult = ([getattr(k, 'v', k) for k in d], list(d.values()), H.log)",
    "values_equal": "log = []\nclass E:\n    def __init__(s, t, v): s.t, s.v = t, v\n    def __eq__(s, o):\n        for _ in (): pass\n        log.append(s.t + o.t)\n        return s.v == o.v\n"
                    "result = ({1: E('a', 1)} == {1: E('b', 1)}, {1: E('c', 1), 2: 3} != {2: 3, 1: E('d', 1)}, {1: 2} == {2: 2}, log)",
    "values_nested_equal": "log = []\nclass E:\n    def __init__(s, t, v): s.t, s.v = t, v\n    def __eq__(s, o):\n        for _ in (): pass\n        log.append(s.t + o.t)\n        return s.v == o.v\n"
                           "result = ([{1: E('a', 1)}] == [{1: E('b', 1)}], {1: (E('c', 1),)} != {1: (E('d', 1),)}, log)",
    "pairs_hashed": "H.log.clear()\nd = dict([(H(1), 'a'), (2, 'b')])\nd.update(zip([H(3), H(1)], 'cd'))\nresult = ([getattr(k, 'v', k) for k in d], list(d.values()), H.log)",
    "fromkeys_hash_fails": "H.log.clear()\ntry: dict.fromkeys((H(1), Unhashed(), H(2)))\nexcept TypeError as e: result = (str(e), H.log)",
    "missing_tuple": "d = Missing({(1, 2): 's'})\nresult = (d[(1, 2)], d[(3,)], d[((1,),)], (3,) not in d)",
    "missing_slot": "d = Missing(a=1)\nresult = (dict.__getitem__(d, 'a'), dict.__getitem__(d, 'b'), d.__getitem__('c'), d.__len__.__self__ is d)",
    "missing_hook": "d = Missing(a=1)\nresult = (d['a'], d['zz' * 1], 'zz' in d, d.get('q'))",
    "keyerror": "result = {}['k']",
    "keyerror_tuple": 'result = {}[(1,)]',
    "unhashable_key": 'result = {[]: 1}',
    "get_default": "result = ({}.get(1), {}.get(1, 'd'), {1: 0}.get(1, 'd'))",
    "pop_default": "d = {1: 2}\nresult = (d.pop(1), d.pop(1, 'd'), d)",
    "pop_missing": 'result = {}.pop(1)',
    "hashed_key_methods": "class K:\n    def __init__(s, n): s.n = n\n    def __hash__(s): log.append(s.n); return s.n\n"
                          "    def __eq__(s, o): return s.n == o.n\nlog = []\nd = {}\nd.setdefault(K(1), 'x')\ns = set()\ns.add(K(2))\n"
                          "result = (d.get(K(1)), d.pop(K(1)), {}.pop(K(3), 0), len(s), log)",
    "equal_key_methods": "class E:\n    def __init__(s, n): s.n = n\n    def __hash__(s): return 1\n    def __eq__(s, o):\n        for _ in range(2): pass\n        log.append(s.n + o.n)\n        return s.n[0] == o.n[0]\nlog = []\nd = {E('a1'): 1}\ns = {E('b1')}\ns.add(E('b2'))\ns.discard(E('c1'))\nresult = (d.get(E('a2')), d.setdefault(E('a3'), 2), d.pop(E('x1'), 0), d.pop(E('a4')), d, len(s), s.remove(E('b3')), s, log)",
    "subclass_equal_key_methods": "class E:\n    def __init__(s, n): s.n = n\n    def __hash__(s): return 1\n    def __eq__(s, o):\n        for _ in range(2): pass\n        log.append(s.n + o.n)\n        return s.n[0] == o.n[0]\nclass D(dict): pass\nlog = []\nd = D({E('a1'): 1, E('b1'): 2})\nresult = (d[E('b2')], E('a3') in d, E('x1') in d, d.get(E('b4')), d.setdefault(E('a5'), 3), d.pop(E('b6')), len(d), log)",
    "subclass_missing_equal_keys": "class E:\n    def __init__(s, n): s.n = n\n    def __hash__(s): return 1\n    def __eq__(s, o):\n        for _ in range(2): pass\n        log.append(s.n + o.n)\n        return s.n[0] == o.n[0]\nclass M(dict):\n    def __missing__(s, k): log.append('missing ' + k.n); return k.n\nlog = []\nd = M({E('a1'): 1})\nv = [d[E('a2')], d[E('b1')]]\nd[E('a3')] = 2\nd[E('c1')] = 3\ndel d[E('c2')]\nresult = (v, sorted(k.n for k in d), list(d.values()), log)",
    "getitem_key_calls": "class E:\n    def __init__(s, n): s.n = n\n    def __hash__(s):\n        for _ in range(2): pass\n        log.append('h' + s.n)\n        return 1\n    def __eq__(s, o):\n        for _ in range(2): pass\n        log.append(s.n + o.n)\n        return s.n[0] == o.n[0]\nclass S(dict):\n    @staticmethod\n    def __missing__(k): return 's' + k.n\nclass C(dict):\n    @classmethod\n    def __missing__(c, k): return c.__name__ + k.n\nlog = []\nd, s, c, t = {E('a1'): 1}, S({E('a2'): 2}), C(), {E('b1')}\nlog.clear()\nv = [dict.__getitem__(d, E('a3')), dict.__getitem__(s, E('b2')), s.__getitem__(E('a4')), c.__getitem__(E('c1')), dict.__getitem__(*(s, E('c2')))]\ntry: set.remove(*(t, E('c3')))\nexcept KeyError: v.append('KeyError')\nresult = (v, log)",
    "subclass_hashed": "class Zero(dict):\n    def __missing__(self, key): return 0\nH.log.clear()\nd, k = Zero(), H(4)\nd[k] = 1\nd[k] += 1\nv = d[k]\nm = d[H(5)]\ndel d[k]\nresult = (v, m, len(d), H.log)",
    "subclass_key_methods": "class E(str):\n    def __hash__(s): return 1\n    def __eq__(s, o):\n        for _ in range(2): pass\n        log.append(str(s) + str(o))\n        return str(s)[0] == str(o)[0]\nlog = []\nd = {E('a1'): 1}\ns = {E('b1')}\ns.add(E('b2'))\ns.discard(E('c1'))\nresult = (d[E('a2')], E('a3') in d, d.get(E('x1')), len(s), sorted(map(str, s)), log)",
    "stored_key_methods": "class E(int):\n    __hash__ = int.__hash__\n    def __eq__(s, o):\n        for _ in range(2): pass\n"
                          "        log.append(int(s) * 10 + o)\n        return int(s) == o\nlog = []\nd = {E(1): 'a'}\ns = {E(2)}\n"
                          "d[1] = 'b'\nresult = (d[1], 1 in d, 2 in s, 3 in s, [type(k).__name__ for k in d], {E(4): 0, 4: 1}[4], log)",
    "tuple_key_hashed": "H.log.clear()\nk = (H(1), (2, H(3)))\nd = {k: 0}\nd[(H(1), (2, H(3)))] += 1\ns = {(H(4),)}\ns.discard((H(4),))\nresult = (d[k], d.get(k), len(s), H.log)",
    "tuple_key_hash_fails": "H.log.clear()\nbad = (H(1), Unhashed())\ntry: {}.get(bad)\nexcept TypeError as e: r = str(e)\ntry: {bad: 0}\nexcept TypeError as e: result = (r, str(e), H.log)",
    "tuple_key_equal": "class E:\n    def __init__(s, n): s.n = n\n    def __hash__(s): return 1\n    def __eq__(s, o):\n        for _ in range(2): pass\n        log.append(s.n + o.n)\n        return s.n[0] == o.n[0]\nlog = []\nk = (E('a1'), 1)\nd = {k: 1, (2, (E('b1'),)): 2, (E('x1'),): 3}\nhash(k)\nk2 = (E('a3'), 1)\nhash(k2)\nresult = (d[(E('a2'), 1)], d.get((2, (E('b2'),))), (E('c1'),) in d, d[k], d.get(k2), len(set([k, k2])), log)",
    "popitem_lifo": 'd = {1: 1, 2: 2, 3: 3}\nresult = (d.popitem(), d.popitem(), d)',
    "popitem_empty": 'result = {}.popitem()',
    "setdefault": "d = {}\nresult = (d.setdefault('a'), d.setdefault('b', 1), d.setdefault('b', 2), d)",
    "ctor_own_keys_calls": "log = []\nclass Own:\n    def __init__(s, ks):\n        def keys():\n            for _ in (): pass\n            log.append('k'); return ks\n        s.keys = keys\n    def __getitem__(s, k):\n        for _ in (): pass\n        log.append(k); return k * 2\nd = {}\nd.update(Own(['a', 'b']))\nresult = (dict(Own(['c'])), d, {**Own(['e'])}, log)",
    "union_keyed": "log = []\nclass K(dict):\n    def __iter__(s): return iter(())\n    def keys(s):\n        for _ in (): pass\n"
                   "        log.append('keys'); return ['b', 'a']\n    def __getitem__(s, k):\n        for _ in (): pass\n        log.append(k); return k * 2\n"
                   "class LD(dict): pass\nx = frozendict(a=1)\nx |= K()\nresult = ({'a': 1, 'q': 0} | K(z=9), x, type(LD(a=1) | K()).__name__, log)",
    "keys_not_iterable": "def make():\n    class Local:\n        def keys(s): return 5\n        def __getitem__(s, k): return k\n    return Local\n"
                         "M = type('M', (make(),), {'__module__': 'pkg'})\nlog = []\nfor v in (make()(), M()):\n"
                         "    try: dict(v)\n    except TypeError as e: log.append(str(e))\nresult = log",
    "ior_keyed_mapping": "log = []\nclass K(dict):\n    def __iter__(s): return iter(())\n    def keys(s):\n        for _ in (): pass\n"
                         "        log.append('keys'); return ['b']\n    def __getitem__(s, k):\n        for _ in (): pass\n        log.append(k); return 2\n"
                         "class L(dict): pass\nd = L(a=1)\nz = d\nd |= K(z=0)\nresult = (d, d is z, dict.__ior__({'a': 1}, K(z=0)), log)",
    "ctor_asked_keys": "log = []\nclass Asked:\n    def __init__(s, has): s.has = has\n    def __getattr__(s, name):\n        for _ in (): pass\n"
                       "        log.append(name)\n        if name == 'keys' and s.has: return lambda: ['a']\n        raise AttributeError(name)\n"
                       "    def __iter__(s): return iter([('x', 1)])\n    def __getitem__(s, k):\n        for _ in (): pass\n        log.append(k); return k * 2\n"
                       "d = {}\nd.update(Asked(True))\nresult = (dict(Asked(True)), dict(Asked(False)), d, log)",
    "ctor_function_keys": "log = []\ndef f(): pass\ndef keys():\n    for _ in (): pass\n    log.append('keys')\n    return ['a']\nf.keys = keys\n"
                          "def text(g):\n    try: g(f)\n    except TypeError as e: return str(e).split(' object is ')[1]\n"
                          "result = (log, text(dict), text(lambda m: {}.update(m)), text(lambda m: {**m}))",
    "ctor_keys_attribute": "class Both:\n    def __iter__(s): return iter([('x', 1)])\n    def keys(s): return ['a']\n    def __getitem__(s, k): return k * 2\n"
                           "class Own(Both):\n    def __init__(s): s.keys = lambda: ['o']\n    keys = None\n"
                           "class Pairs:\n    def __iter__(s): yield ('p', 1)\n"
                           "result = [dict(Both()), dict(Pairs()), dict(Own())]",
    "ctor_keys_listed": "log = []\nclass M:\n    def keys(s):\n        for k in 'ab':\n            log.append('k' + k)\n            yield k\n"
                        "    def __getitem__(s, k):\n        log.append('g' + k)\n        return k.upper()\n"
                        "result = (dict(M()), {}.update(M()), log)",
    "update_forms": "d = {}\nd.update({'a': 1}, b=2)\nd.update([('c', 3)])\nd.update(KeysOnly())\nresult = d",
    "update_bad": 'result = {}.update(1)',
    "update_too_many": 'result = {}.update({}, {})',
    "or_non_dict": 'result = {} | [1]',
    "ior_explicit": "class M:\n    def keys(s):\n        for _ in range(2): pass\n        log.append('keys')\n        return ['a', 'b']\n    def __getitem__(s, k):\n        for _ in range(2): pass\n        log.append(k)\n        return k * 2\nclass LD(dict): pass\nlog = []\nd = {'z': 0}\ne = LD(y=1)\nresult = (dict.__ior__(d, M()) is d, d, e.__ior__(M()) is e, e, dict.__ior__({}, [('p', 1)]), log)",
    "ior_iterable": "d = {}\nd |= [('a', 1)]\nresult = d",
    "merge_dict_iter": "log = []\nclass D(dict):\n    def keys(s):\n        for _ in (): pass\n        log.append('keys')\n        return ['a']\n"
                       "    def __getitem__(s, k):\n        for _ in (): pass\n        log.append(k)\n        return k * 2\n"
                       "class Own(D):\n    def __iter__(s): return iter(['z'])\n"
                       "u = {}\nu.update(Own(q=1))\nresult = ({**D(q=1)}, {**Own(q=1)}, u, log)",
    "ior_mapping": "class M:\n    def keys(s):\n        for _ in range(2): pass\n        log.append('keys')\n        return ['a', 'b']\n    def __getitem__(s, k):\n        for _ in range(2): pass\n        log.append(k)\n        return k * 2\nlog = []\nd = e = {'z': 0}\nd |= M()\nresult = (d, d is e, log)",
    "merge_equal_keys": "class E:\n    def __init__(s, n): s.n = n\n    def __hash__(s): return 1\n    def __eq__(s, o):\n        for _ in range(2): pass\n        log.append(s.n + o.n)\n        return s.n[0] == o.n[0]\nlog = []\nd = {E('a1'): 1}\ndel log[:]\nd.update({E('a2'): 2, E('b1'): 3})\nd |= {E('b2'): 4}\nf = d | {E('c1'): 5}\ng = {**d, **{E('a3'): 6}}\nresult = ([(k.n, v) for k, v in d.items()], len(f), [(k.n, v) for k, v in g.items()], log)",
    "merge_mutated": "class E:\n    def __init__(s, n): s.n = n\n    def __hash__(s): return 1\n    def __eq__(s, o):\n        src.clear() if o.n == 'b' else src.update(z=0)\n        return False\nsrc = {}\nout = []\nfor k in ('a', 'b'):\n    d = {E('x'): 0}\n    src.clear()\n    src[E(k)] = 1\n    try:\n        d.update(src)\n    except RuntimeError as e:\n        out.append((str(e), len(d)))\nresult = out",
    "merge_empty": "class E:\n    def __init__(s, n): s.n = n\n    def __hash__(s): return 1\n    def __eq__(s, o):\n        for _ in range(2): pass\n        log.append(s.n + o.n)\n        return s is o\nclass D(dict): pass\nlog = []\nd = {E('a'): 1, E('b'): 2, E('c'): 3}\ndel log[:]\nn = [len(dict(d)), len({**d}), len(D(d)), len(d.copy()), len(d | {})]\ne = {}\ne.update(d)\nf = {0: 0}\nf.update(d)\nresult = (n, len(e), len(f), log)",
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
