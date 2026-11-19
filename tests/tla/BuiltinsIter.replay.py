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
    "enumerate_start_first": "log = []\n"
                             "class I:\n"
                             "    def __iter__(self):\n"
                             "        for _ in (): pass\n"
                             "        log.append('iter')\n"
                             "        return iter('ab')\n"
                             "class N:\n"
                             "    def __index__(self):\n"
                             "        for _ in (): pass\n"
                             "        log.append('index')\n"
                             "        return 3\n"
                             "result = (list(enumerate(I(), N())), list(enumerate(I(), start=N())), log)",
    "iter_sequence_protocol": 'result = (list(iter(Seq())), list(reversed(Seq())), 20 in Seq())',
    "reversed_hook": 'result = list(reversed(Rev()))',
    "reversed_len": "log = []\nclass S:\n    def __init__(s, n): s.n = n\n    def __len__(s):\n        for _ in (): pass\n"
                    "        log.append(s.n)\n        return s.n\n    def __getitem__(s, i): return i\n"
                    "class N:\n    def __getitem__(s, i): return i\n"
                    "try: reversed(S(-1))\nexcept ValueError: log.append('neg')\n"
                    "try: reversed(N())\nexcept TypeError: log.append('nolen')\n"
                    "result = ([x for x in reversed(S(3))], log)",
    "reversed_bad": 'result = reversed({1, 2})',
    "reversed_dict": 'result = list(reversed({1: 2, 3: 4}))',
    "next_default": "it = iter([1])\nresult = (next(it), next(it, 'end'), next(it, None))",
    "next_python": "class C:\n    def __init__(s, n): s.n = n\n    def __next__(s):\n        for _ in (): pass\n"
                   "        if not s.n: raise StopIteration\n        s.n -= 1\n        return s.n\n"
                   "c = C(1)\nresult = (next(c), next(c, 'end'), next(C(0), None))",
    "next_called": "class S:\n    def __getitem__(s, i):\n        for _ in (): pass\n        if i > 0: raise IndexError\n        return i\n"
                   "def f(x):\n    for _ in (): pass\n    if x == 's': raise StopIteration\n    return x * 2\n"
                   "it = iter(S())\nresult = (next(it), next(it, 'end'), next(map(f, [2])), next(map(f, 's'), 'stop'), next(filter(f, [0, 3])))",
    "star_called": "log = []\nclass S:\n    def __getitem__(s, i):\n        for _ in (): pass\n        if i > 1: raise IndexError\n        return i\n"
                   "    def __len__(s):\n        for _ in (): pass\n        log.append('len')\n        return 2\n"
                   "def g(x):\n    for _ in (): pass\n    return x + 1\n"
                   "def f(): return [*iter(S())], (*map(g, [1]),), (*reversed(S()),), len(log)\nresult = f()",
    "next_retry": "class S:\n    f = 1\n    def __getitem__(s, i):\n        for _ in (): pass\n"
                  "        if S.f:\n            S.f = 0\n            raise KeyError(i)\n        if i > 1: raise IndexError\n        return i\n"
                  "it = iter(S())\ntry: next(it)\nexcept KeyError: pass\nresult = list(it)",
    "adapt_python": "class C:\n    def __init__(s, n): s.n = n\n    def __iter__(s): return s\n    def __next__(s):\n        for _ in (): pass\n"
                    "        if not s.n: raise StopIteration\n        s.n -= 1\n        return s.n\n"
                    "result = (list(enumerate(C(2))), list(zip('ab', C(3))), list(map(abs, C(1))), next(zip(C(1), C(0)), 'end'))",
    "adapt_iter": "log = []\nclass C:\n    def __init__(s, *v): s.v = v\n    def __iter__(s):\n        for _ in (): pass\n"
                  "        log.append(s.v)\n        if not s.v: raise KeyError('k')\n        return iter(s.v)\n"
                  "try: zip(C(1), C(), C(2))\nexcept KeyError: pass\n"
                  "result = (list(zip(C(1), [2], C(3))), list(map(abs, C(4))), list(enumerate(C(5))), list(filter(None, C(0, 6))), log)",
    "adapt_iter_strict": "log = []\nclass C:\n    def __init__(s, *v): s.v = v\n    def __iter__(s):\n        for _ in (): pass\n"
                         "        log.append(s.v)\n        return iter(s.v)\n"
                         "try: list(zip(C(1), C(2, 3), strict=True))\nexcept ValueError as e: r = str(e)\n"
                         "result = (r, list(map(max, C(4), C(5), strict=1)), log)",
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
    "map_repr": "log = []\nclass R:\n    def __repr__(s):\n        for _ in (): pass\n        log.append(1)\n        return 'r'\n"
                "result = (list(map(repr, [[R()], (R(),)])), list(map(ascii, [[R()]])), len(log))",
    "map_generator": "log = []\ndef g():\n    try:\n        x = yield 0\n        log.append((x, 0))\n        yield x\n    finally:\n        log.append('fin')\n"
                     "gs = [g(), g()]\nh = g()\nnext(h)\n"
                     "result = (list(map(next, gs)), list(map(type(h).send, gs, 'ab')), list(map(type(h).close, [h])), log)",
    "map_bound": "class K:\n    def __init__(s, k): s.k = k\n    def add(s, v): return s.k + v\n    def __call__(s, v, w): return s.k * v + w\n"
                 "result = (list(map(K(2).add, [1, 3])), list(map(K(10), [1, 2], [2])))",
    "map_convert": "log = []\nclass K:\n    def __init__(s, v): s.v = v\n    def __str__(s):\n        for _ in (): pass\n"
                   "        log.append('s%d' % s.v)\n        return 'k%d' % s.v\n"
                   "    def __repr__(s):\n        for _ in (): pass\n        log.append('r%d' % s.v)\n        return 'K%d' % s.v\n"
                   "    def __format__(s, spec):\n        for _ in (): pass\n        log.append('f')\n        return 'F' + spec\n"
                   "a, b = K(1), K(2)\n"
                   "result = (list(map(str, [a, b])), list(map(repr, (a, 7))), ','.join(map(str, iter([a, b]))), list(map(format, [a])), log)",
    "map_adapted": "log = []\nclass S:\n    def __init__(s, v): s.v = v\n    def __str__(s):\n        for _ in (): pass\n        log.append(s.v)\n        return str(s.v)\nresult = (list(zip('ab', map(str, [S(1), S(2)]))), list(enumerate(map(str, [S(3)]))), log)",
    "sorted_later_calls": "log = []\nclass P:\n    def __init__(s, v): s.v = v\n"
                          "    def __eq__(s, o):\n        for _ in (): pass\n        log.append('=' + str(s.v)); return s.v == o.v\n"
                          "    def __lt__(s, o):\n        for _ in (): pass\n        log.append('<' + str(s.v)); return s.v < o.v\n"
                          "result = ([t[0] for t in sorted([(0, P(2)), (1, P(3)), (1, P(1))])], [t[0][0] for t in sorted([((1, P(2)),), ((1, P(1)),)])], log)",
    "sorted_sources": "log = []\nclass O:\n    def __init__(s, v): s.v = v\n    def __hash__(s): return s.v\n    def __lt__(s, o):\n        for _ in (): pass\n        log.append(s.v)\n        return s.v < o.v\n"
                      "it = iter([O(9), O(4), O(2)])\nnext(it)\nv = lambda l: [o.v for o in l]\n"
                      "result = (v(sorted({O(3), O(1), O(2)})), v(sorted({O(1): 0, O(3): 0}.keys(), reverse=True)), v(sorted(it)), log != [])",
    "starred_calls": "log = []\nclass B:\n    def __init__(s, v): s.v = v\n    def __bool__(s):\n        for _ in (): pass\n        log.append(s.v)\n        return bool(s.v)\n"
                     "class W:\n    def __str__(s):\n        for _ in (): pass\n        log.append('str')\n        return 's'\n    def __format__(s, f):\n        for _ in (): pass\n        log.append('format')\n        return 'f'\n"
                     "result = (any(*[[B(0), B(1), B(2)]]), str(*[W()]), format(*(W(), '')), log)",
    "zip_callable": "log = []\nn = [0]\ndef f():\n    for _ in (): pass\n    n[0] += 1\n    log.append(n[0])\n    return n[0] % 3\n"
                    "a = [p for p in zip('xyz', iter(f, 0))]\nn[0] = 0\nb = list(enumerate(iter(f, 0)))\n"
                    "result = (a, b, log)",
    "callable_sentinel_eq": "log = []\nclass S:\n    def __init__(s, n): s.n = n\n    def __eq__(s, o):\n        for _ in (): pass\n"
                            "        log.append((s.n, o))\n        return o == s.n\n"
                            "def counter(xs):\n    it = iter(xs)\n    return lambda: next(it)\n"
                            "result = (list(iter(counter([1, 2, 3, 4]), S(3))), [x for x in iter(counter([0, 1]), S(1))], log)",
    "zip_sentinel_eq": "log = []\nclass S:\n    def __init__(s, n): s.n = n\n    def __eq__(s, o):\n        for _ in (): pass\n"
                       "        log.append((s.n, o))\n        return o == s.n\n"
                       "def counter(xs):\n    it = iter(xs)\n    return lambda: next(it)\n"
                       "result = (list(zip(iter(counter([1, 2, 3]), S(3)), 'abc')), [x for x in enumerate(iter(counter([4, 5]), S(5)))], log)",
    "callable_calls": "log = []\nn = [0]\ndef f():\n    for _ in (): pass\n    n[0] += 1\n    log.append(n[0])\n    return n[0] % 3\n"
                      "a = [x for x in iter(f, 0)]\nn[0] = 0\nb = sum(iter(f, 0))\nn[0] = 0\nc = list(iter(f, 0))\nn[0] = 0\n"
                      "result = (a, b, c, next(iter(f, 0)), log)",
    "map_hash_tuple": "log = []\nclass H:\n    def __init__(s, v): s.v = v\n    def __hash__(s):\n        for _ in (): pass\n        log.append(s.v)\n        return s.v\nresult = (list(map(hash, [(H(1),), (2, (H(3), H(4)))])) == [hash((1,)), hash((2, (3, 4)))], log)",
    "map_class": "log = []\nclass P:\n    def __init__(s, *a):\n        for _ in (): pass\n        log.append(a[0])\n        s.a = a\n"
                 "out = []\nfor p in map(P, [1, 2], 'ab'):\n    out.append(p.a)\n    log.append(('t', p.a[0]))\nresult = (out, log)",
    "map_class_new": "log = []\nclass Q:\n    def __new__(cls, *a):\n        for _ in (): pass\n        log.append(('n', a[0]))\n"
                     "        return 'z' if a == (0,) else super().__new__(cls)\n"
                     "    def __init__(s, *a):\n        for _ in (): pass\n        log.append(('i', a[0]))\n        s.a = a[0]\n"
                     "result = ([q if q == 'z' else q.a for q in map(Q, [0, 2, 3])], log)",
    "map_class_bad": "class B:\n    def __init__(s, v):\n        for _ in (): pass\n        return v\nresult = list(map(B, [None, 1]))",
    "map_convert_bad": "class W:\n    def __str__(s):\n        for _ in (): pass\n        return 1\nresult = list(map(str, [W()]))",
    "sort_key_callables": "class R:\n    def __init__(s, v): s.v = -v\n    def __lt__(s, o): return s.v < o.v\n"
                          "class W:\n    def m(s, v): return v % 2\n    def __call__(s, v): return -v\n"
                          "result = (sorted([1, 3, 2], key=R), sorted([1, 2, 3, 4], key=W().m), max([1, 3, 2], key=W()))",
    "filter_builtin": "class F:\n    def __init__(s, n): s.n = n\n    def __len__(s):\n        for _ in (): pass\n"
                      "        log.append(('len', s.n))\n        return s.n\nlog = []\n"
                      "result = ([x if x == 'a' else x.n for x in filter(len, [F(1), '', F(0), 'a', F(2)])], log)",
    "sort_builtin_keys": "class K:\n    def __init__(s, n): s.n = n\n    def __len__(s):\n        for _ in (): pass\n"
                         "        log.append(s.n)\n        return s.n\n    def __repr__(s):\n        for _ in (): pass\n"
                         "        return 'k%d' % s.n\nlog = []\nks = [K(3), K(1), K(2)]\nks.sort(key=len)\n"
                         "result = (sorted([K(2), 'a', K(0)], key=len), max(ks, key=repr), min(K(4), K(5), key=len), ks, log)",
    "builtin_key_iterators": "class K:\n    def __init__(s, n): s.n = n\n    def __len__(s):\n        for _ in (): pass\n"
                             "        log.append(s.n)\n        return s.n\n    def __repr__(s): return 'k%d' % s.n\n"
                             "    def __hash__(s): return s.n\nlog = []\nks = [K(3), K(1), K(2)]\nit = iter(ks)\n"
                             "result = (sorted(iter(ks), key=len), max(iter(tuple(ks)), key=len), (next(it), sorted(it, key=len))[1], "
                             "sorted({K(5): 0, K(4): 1}, key=len), log)",
    "key_sources": "def g(n):\n    for i in range(n):\n        log.append(i)\n        yield i\nlog = []\n"
                   "def k(v):\n    log.append('k%d' % v)\n    return -v\n"
                   "result = (sorted(g(2), key=k), max(g(2), key=k), min(g(0), key=k, default='d'), log)",
    "consume_getitem": "class G:\n    def __getitem__(s, i):\n        if i >= 3: raise IndexError(i)\n        return i\n"
                       "class L(G):\n    def __len__(s): return 3\n"
                       "result = (list(G()), sum(G()), sorted(G()), [x for x in G()], tuple(iter(G())), list(reversed(L())))",
    "filter_next": "log = []\nclass N:\n    def __init__(s, *v): s.v = list(v)\n    def __iter__(s): return s\n    def __next__(s):\n        for _ in (): pass\n        if not s.v: raise StopIteration\n        log.append(s.v[0]); return s.v.pop(0)\nclass T:\n    def __init__(s, v): s.v = v\n    def __bool__(s): log.append('b%d' % s.v); return bool(s.v)\nresult = (list(filter(None, N(0, 1, 2))), [t.v for t in filter(bool, N(T(0), T(1)))], list(filter(abs, N(0, -3))), next(filter(lambda x: x > 1, N(1, 2))), len(log))",
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
    "sort_tuple_lt_only": 'class L:\n    def __init__(self, v): self.v = v\n'
                          '    def __lt__(self, o):\n        for _ in (): pass\n        log.append(1)\n        return self.v < o.v\nlog = []\n'
                          'ts = [(L(2), 0), (L(0), 1), (L(1), 2)]\nts.sort()\n'
                          'result = ([t[0].v for t in ts], [t[0].v for t in sorted(ts, reverse=True)], bool(log))',
    "sort_list_ties": 'class T:\n    def __init__(self, v, home=None): self.v = v; self.home = home\n'
                      '    def __eq__(self, o):\n        log.append(1)\n        if self.home is not None: self.home.clear()\n        return self.v == o.v\n'
                      '    def __lt__(self, o): return self.v < o.v\nlog = []\n'
                      'def homed(v):\n    l = []\n    l.append(T(v, l)); l.append(v)\n    return l\nls = [homed(1), homed(1), homed(1)]\n'
                      'result = ([l[1].v for l in sorted([[0, T(2)], [0, T(1)], [0, T(0)]])], bool(log), sorted(map(id, sorted(ls))) == sorted(map(id, ls)))',
    "filter_generator": "log = []\ndef g(n):\n    for i in range(n):\n        log.append(i)\n        yield i\n"
                        "def odd(x):\n    log.append(-x)\n    return x % 2\nresult = (list(filter(odd, g(4))), log)",
    "zip_native_generator": "log = []\ndef g(n):\n    for i in range(n):\n        log.append(i)\n        yield i\n"
                            "it = iter('abc')\nz = list(zip('ab', g(5))), dict(zip(b'x', g(2)))\nlist(zip(it, g(1)))\nresult = z + (next(it), log)",
    "sort_lt_declined": "class D:\n    def __init__(self, v): self.v = v\n    def __lt__(self, o): return NotImplemented\n"
                        "    def __eq__(self, o): return NotImplemented\n    def __gt__(self, o):\n        for _ in (): pass\n"
                        "        if self.v == 9: raise KeyError\n        return self.v > o.v\n"
                        "try: sorted([D(9), D(1)])\nexcept KeyError as e: err = type(e).__name__\n"
                        "result = ([x.v for x in sorted([D(2), D(3), D(1)])], [t[1] for t in sorted([(D(1), 0), (D(0), 1)], reverse=True)], err)",
    "min_reflected_truth": "log = []\nclass T:\n    def __init__(self, v): self.v = v\n"
                           "    def __bool__(self):\n        for _ in (): pass\n        log.append('bool'); return self.v\n"
                           "class O:\n    def __init__(self, v): self.v = v\n"
                           "    def __lt__(self, o): log.append('lt'); return NotImplemented\n"
                           "    def __gt__(self, o):\n        for _ in (): pass\n        log.append('gt'); return T(self.v > o.v)\n"
                           "result = (min([O(2), O(1)]).v, max(O(1), O(3)).v, log)",
    "sort_truth": "log = []\nclass T:\n    def __init__(self, v): self.v = v\n"
                  "    def __bool__(self):\n        for _ in (): pass\n        log.append('bool'); return self.v\n"
                  "class O:\n    def __init__(self, v): self.v = v\n"
                  "    def __lt__(self, o): log.append('lt'); return T(self.v < o.v)\n"
                  "    def __eq__(self, o): log.append('eq'); return T(self.v == o.v)\n"
                  "result = ([o.v for o in sorted([O(2), O(1)])], [(a.v, b) for a, b in sorted([(O(1), 2), (O(1), 1)])], log)",
    "max_key_truth": "log = []\nclass T:\n    def __init__(self, v): self.v = v\n"
                     "    def __bool__(self):\n        for _ in (): pass\n        log.append('bool'); return self.v\n"
                     "class L:\n    def __init__(self, n): self.n = n\n"
                     "    def __lt__(self, o):\n        for _ in (): pass\n        log.append('lt'); return T(self.n < o.n)\n"
                     "result = (max([1, 3, 2], key=L), log)",
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
