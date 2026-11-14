# Replays BuiltinsIter.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
class Seq:
    def __len__(self): return 3
    def __getitem__(self, i):
        if i >= 3: raise IndexError
        return i * 10
class Rev:
    def __reversed__(self): return iter("rev")
class NegLen:
    def __len__(self): return -1
class BigLen:
    def __len__(self): return 2 ** 70
class FloatLen:
    def __len__(self): return 1.0
class Mutator:
    def __init__(self, v, l): self.v, self.l = v, l
    def __lt__(self, other):
        self.l.append(0)
        return self.v < other.v
LISTS = [()]
for n in range(1, 5):
    LISTS += [l + (x,) for l in LISTS if len(l) == n - 1 for x in (1, 2, 3)]
OPS = ["sorted", "sorted_rev", "reversed", "enumerate", "zip_strict", "filter", "map", "any_all", "iter_sentinel", "max_key"]


def iterate(op, l):
    l = list(l)
    try:
        if op == "sorted": return repr([i for k, i in sorted([(k, i) for i, k in enumerate(l)], key=lambda p: p[0])])
        if op == "sorted_rev": return repr([i for k, i in sorted([(k, i) for i, k in enumerate(l)], key=lambda p: p[0], reverse=True)])
        if op == "reversed": return repr(list(reversed(l)))
        if op == "enumerate": return repr(list(enumerate(l, 1)))
        if op == "zip_strict": return repr(list(zip(l, l[:2], strict=True)))
        if op == "filter": return repr(list(filter(lambda x: x != 2, l)))
        if op == "map": return repr(list(map(lambda a, b: a * b, l, l[1:])))
        if op == "any_all":
            it = iter(l)
            found = any(x == 3 for x in it)
            rest = len(list(it))
            it = iter(l)
            return repr((found, rest, all(x < 3 for x in it), len(list(it))))
        if op == "iter_sentinel":
            it = iter(l)
            return repr(list(iter(lambda: next(it), 2)))
        if op == "max_key": return repr(max(range(len(l)), key=lambda i: l[i], default=-1))
    except ValueError as error:
        return "ValueError: %s" % error

SOURCES = {
    "iter_sequence_protocol": 'result = (list(iter(Seq())), list(reversed(Seq())), 20 in Seq())',
    "reversed_hook": 'result = list(reversed(Rev()))',
    "reversed_bad": 'result = reversed({1, 2})',
    "reversed_dict": 'result = list(reversed({1: 2, 3: 4}))',
    "next_default": "it = iter([1])\nresult = (next(it), next(it, 'end'), next(it, None))",
    "next_python": "class C:\n    def __init__(s, n): s.n = n\n    def __next__(s):\n        for _ in (): pass\n"
                   "        if not s.n: raise StopIteration\n        s.n -= 1\n        return s.n\n"
                   "c = C(1)\nresult = (next(c), next(c, 'end'), next(C(0), None))",
    "adapt_python": "class C:\n    def __init__(s, n): s.n = n\n    def __iter__(s): return s\n    def __next__(s):\n        for _ in (): pass\n"
                    "        if not s.n: raise StopIteration\n        s.n -= 1\n        return s.n\n"
                    "result = (list(enumerate(C(2))), list(zip('ab', C(3))), list(map(abs, C(1))), next(zip(C(1), C(0)), 'end'))",
    "adapt_iter": "log = []\nclass C:\n    def __init__(s, *v): s.v = v\n    def __iter__(s):\n        for _ in (): pass\n"
                  "        log.append(s.v)\n        if not s.v: raise KeyError('k')\n        return iter(s.v)\n"
                  "try: zip(C(1), C(), C(2))\nexcept KeyError: pass\n"
                  "result = (list(zip(C(1), [2], C(3))), list(map(abs, C(4))), list(enumerate(C(5))), list(filter(None, C(0, 6))), log)",
    "next_stop": 'result = next(iter([]))',
    "next_non_iterator": 'result = next([1])',
    "iter_sentinel_noncallable": 'result = iter(1, 2)',
    "iter_two_args_kw": 'result = iter(int, sentinel=0)',
    "zip_strict_first_shorter": 'result = list(zip([1], [1, 2], strict=True))',
    "zip_strict_third": 'result = list(zip([1, 2], [1, 2], [1], strict=True))',
    "zip_shortest": "result = (list(zip('ab', range(5))), list(zip()), list(zip('a')))",
    "zip_consumes": 'it = iter([1, 2, 3])\nlist(zip(it, []))\nresult = list(it)',
    "zip_consumes_order": 'it = iter([1, 2, 3])\nlist(zip([], it))\nresult = list(it)',
    "map_strict": 'result = list(map(pow, [1, 2], [3], strict=True))',
    "map_shortest": 'result = list(map(pow, [2, 3, 4], [1, 2]))',
    "map_none": 'result = list(map(None, [1]))',
    "map_bound": "class K:\n    def __init__(s, k): s.k = k\n    def add(s, v): return s.k + v\n    def __call__(s, v, w): return s.k * v + w\n"
                 "result = (list(map(K(2).add, [1, 3])), list(map(K(10), [1, 2], [2])))",
    "map_convert": "log = []\nclass K:\n    def __init__(s, v): s.v = v\n    def __str__(s):\n        for _ in (): pass\n"
                   "        log.append('s%d' % s.v)\n        return 'k%d' % s.v\n"
                   "    def __repr__(s):\n        for _ in (): pass\n        log.append('r%d' % s.v)\n        return 'K%d' % s.v\n"
                   "    def __format__(s, spec):\n        for _ in (): pass\n        log.append('f')\n        return 'F' + spec\n"
                   "a, b = K(1), K(2)\n"
                   "result = (list(map(str, [a, b])), list(map(repr, (a, 7))), ','.join(map(str, iter([a, b]))), list(map(format, [a])), log)",
    "map_adapted": "log = []\nclass S:\n    def __init__(s, v): s.v = v\n    def __str__(s):\n        for _ in (): pass\n        log.append(s.v)\n        return str(s.v)\nresult = (list(zip('ab', map(str, [S(1), S(2)]))), list(enumerate(map(str, [S(3)]))), log)",
    "sorted_sources": "log = []\nclass O:\n    def __init__(s, v): s.v = v\n    def __hash__(s): return s.v\n    def __lt__(s, o):\n        for _ in (): pass\n        log.append(s.v)\n        return s.v < o.v\n"
                      "it = iter([O(9), O(4), O(2)])\nnext(it)\nv = lambda l: [o.v for o in l]\n"
                      "result = (v(sorted({O(3), O(1), O(2)})), v(sorted({O(1): 0, O(3): 0}.keys(), reverse=True)), v(sorted(it)), log != [])",
    "map_hash_tuple": "log = []\nclass H:\n    def __init__(s, v): s.v = v\n    def __hash__(s):\n        for _ in (): pass\n        log.append(s.v)\n        return s.v\nresult = (list(map(hash, [(H(1),), (2, (H(3), H(4)))])) == [hash((1,)), hash((2, (3, 4)))], log)",
    "map_convert_bad": "class W:\n    def __str__(s):\n        for _ in (): pass\n        return 1\nresult = list(map(str, [W()]))",
    "sort_key_callables": "class R:\n    def __init__(s, v): s.v = -v\n    def __lt__(s, o): return s.v < o.v\n"
                          "class W:\n    def m(s, v): return v % 2\n    def __call__(s, v): return -v\n"
                          "result = (sorted([1, 3, 2], key=R), sorted([1, 2, 3, 4], key=W().m), max([1, 3, 2], key=W()))",
    "key_sources": "def g(n):\n    for i in range(n):\n        log.append(i)\n        yield i\nlog = []\n"
                   "def k(v):\n    log.append('k%d' % v)\n    return -v\n"
                   "result = (sorted(g(2), key=k), max(g(2), key=k), min(g(0), key=k, default='d'), log)",
    "consume_getitem": "class G:\n    def __getitem__(s, i):\n        if i >= 3: raise IndexError(i)\n        return i\n"
                       "class L(G):\n    def __len__(s): return 3\n"
                       "result = (list(G()), sum(G()), sorted(G()), [x for x in G()], tuple(iter(G())), list(reversed(L())))",
    "filter_none": "result = list(filter(None, [0, 1, '', 'a', None, []]))",
    "filter_truth": "log = []\nclass T:\n    def __init__(s, v): s.v = v\n    def __bool__(s):\n        for _ in (): pass\n"
                    "        log.append('b%d' % s.v)\n        return s.v > 0\n"
                    "class L:\n    def __init__(s, v): s.v = v\n    def __len__(s):\n        for _ in (): pass\n"
                    "        log.append('l%d' % s.v)\n        return s.v\n"
                    "result = ([x.v for x in filter(None, [T(1), T(0), 0, L(3)])], [x.v for x in filter(bool, (T(0), T(1)))], log)",
    "filter_truth_bad": "class Bad:\n    def __bool__(s):\n        for _ in (): pass\n        return 1\nresult = list(filter(None, [Bad()]))",
    "enumerate_kw": "result = (list(enumerate('ab', start=-1)), list(enumerate(iterable='a')))",
    "enumerate_bad_start": "result = enumerate('a', 1.5)",
    "all_any_empty": "result = (all([]), any([]), all([0, 1/1]), any(iter([0, '', 2])))",
    "all_returns_bool": "result = (all([1, 'x']), any([0, 'x']))",
    "sorted_key_none": "result = (sorted('bca', key=None), sorted([3, 1, 2], reverse=1))",
    "sorted_positional_key": 'result = sorted([1], None)',
    "sorted_mixed": "result = sorted([1, 'a'])",
    "sorted_returns_new": 'a = [3, 1]\nb = sorted(a)\nresult = (a, b, a is b)',
    "list_sort_none": 'a = [2, 1]\nresult = (a.sort(), a)',
    "sort_stability_doc": "data = [('red', 1), ('blue', 1), ('red', 2), ('blue', 2)]\nresult = sorted(data, key=lambda t: t[0])",
    "sort_reverse_stable": "result = sorted([(1, 'a'), (0, 'b'), (1, 'c')], key=lambda t: t[0], reverse=True)",
    "sort_mutated": 'l = []\nl.extend(Mutator(v, l) for v in (2, 1))\nl.sort()',
    "sort_key_error": 'result = sorted([1, 2], key=lambda x: 1 / (x - 1))',
    "sort_lt_only": 'class L:\n    def __init__(self, v): self.v = v\n    def __lt__(self, o): return self.v < o.v\nresult = [x.v for x in sorted([L(2), L(1), L(3)])]',
    "sort_tuple_ties": 'class T:\n    def __init__(self, v): self.v = v\n    def __eq__(self, o): log.append(1); return self.v == o.v\n'
                       '    def __lt__(self, o): return self.v < o.v\nlog = []\n'
                       'result = ([t[1].v for t in sorted([(0, T(2)), (0, T(1)), (0, T(0))])], bool(log))',
    "sort_gt_reflected": 'class G:\n    def __init__(self, v): self.v = v\n    def __gt__(self, o): return self.v > o.v\nresult = [x.v for x in sorted([G(2), G(1)])]',
    "len_negative": 'result = len(NegLen())',
    "len_big": 'result = len(BigLen())',
    "len_float": 'result = len(FloatLen())',
    "len_unsized": 'result = len(5)',
    "sum_iter": 'result = sum(x * x for x in range(4))',
    "aiter_sync": 'result = aiter([])',
    "slice_builtin": 'result = ([0, 1, 2, 3][slice(1, None, 2)], slice(3).indices(10), repr(slice(1, 2)))',
    "range_iter_type": 'result = type(iter(range(3))).__name__',
    "iter_sentinel_reentrant": ("calls = []\n"
                                "def f():\n"
                                "    calls.append(0)\n"
                                "    if len(calls) > 1: return 'stop'\n"
                                "    list(it)\n"
                                "    return 'more'\n"
                                "it = iter(f, 'stop')\n"
                                "result = (list(it), len(calls), it.__reduce__()[1])"),
    "iter_sentinel_reduce": "it = iter(int, 1)\nresult = it.__reduce__()[1]",
    "iter_sequence_state": ("class S:\n"
                            "    def __getitem__(self, i):\n"
                            "        if i < 4: return i\n"
                            "        raise IndexError\n"
                            "it = iter(S())\n"
                            "next(it)\n"
                            "a = it.__reduce__()[2]\n"
                            "it.__setstate__(-3)\n"
                            "b = next(it)\n"
                            "it.__setstate__(3)\n"
                            "result = (a, b, list(it), it.__reduce__()[1])"),
}


TYPES = {name: value for name, value in list(globals().items()) if isinstance(value, type) and name[0].isupper()}


def generated(p):
    return iterate(p["op"], p["l"])


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
