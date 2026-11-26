# Replays Iterators.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
class NonIter:
    def __iter__(self): return 5
class NoNext:
    def __iter__(self): return self
class IterNone:
    __iter__ = None
class Plain:
    pass
class Revival:
    def __init__(self): self.calls = 0
    def __iter__(self): return self
    def __next__(self):
        self.calls += 1
        if self.calls == 2: raise StopIteration
        return self.calls
class Both:
    def __iter__(self): return iter([1, 2])
    def __getitem__(self, i): return 'item'
class SeqIndexError:
    def __getitem__(self, i):
        if i > 1: raise IndexError
        return i
class SeqStopIteration:
    def __getitem__(self, i):
        if i > 0: raise StopIteration
        return i
class SeqLookupError:
    def __getitem__(self, i): raise KeyError(i)

KINDS = ["list", "tuple", "str", "bytes", "bytearray", "dict", "dict_values", "dict_items", "set", "frozenset", "range",
         "reversed", "enumerate", "zip", "map", "filter", "generator", "callable_iterator", "sequence_protocol",
         "custom_iterator", "genexpr", "memoryview"]


class Seq:
    def __init__(self, items): self.items = items
    def __getitem__(self, i): return self.items[i]
    def append(self, x): self.items.append(x)


class Counter:
    def __init__(self, items): self.items = items; self.i = 0
    def __iter__(self): return self
    def __next__(self):
        if self.i >= len(self.items): raise StopIteration
        self.i += 1
        return self.items[self.i - 1]


def make(kind, n):
    items = [10, 20][:n]
    if kind == "list": src = list(items); return src, iter(src), lambda: src.append(30)
    if kind == "tuple": return None, iter(tuple(items)), None
    if kind == "str": return None, iter("ab"[:n]), None
    if kind == "bytes": return None, iter(bytes(items)), None
    if kind == "bytearray": src = bytearray(items); return src, iter(src), lambda: src.append(30)
    if kind == "dict": src = dict.fromkeys(items); return src, iter(src), None
    if kind == "dict_values": return None, iter({i: i + 1 for i in items}.values()), None
    if kind == "dict_items": return None, iter({i: i + 1 for i in items}.items()), None
    if kind == "set": return None, iter(sorted(set(items))), None
    if kind == "frozenset": f = frozenset(items); return None, iter(f if n < 2 else sorted(f)), None
    if kind == "range": return None, iter(range(10, 10 + 10 * n, 10)), None
    if kind == "reversed": src = list(items); return src, reversed(src), lambda: src.append(30)
    if kind == "enumerate": return None, enumerate(items), None
    if kind == "zip": return None, zip(items, items), None
    if kind == "map": return None, map(str, items), None
    if kind == "filter": return None, filter(None, items + [0]), None
    if kind == "generator":
        def gen():
            yield from items
        return None, gen(), None
    if kind == "callable_iterator": it = iter(items + [None]); return None, iter(lambda: next(it), None), None
    if kind == "sequence_protocol": src = Seq(list(items)); return src, iter(src), lambda: src.append(30)
    if kind == "custom_iterator": return None, Counter(items), None
    if kind == "genexpr": return None, (x for x in items), None
    if kind == "memoryview": src = bytearray(items); return None, iter(memoryview(src)), None


def run(kind, n):
    _, it, grow = make(kind, n)
    log = [iter(it) is it]
    for _ in range(n + 2):
        try:
            log.append(next(it))
        except StopIteration:
            log.append("stop")
    if grow:
        grow()
        try:
            log.append(next(it))
        except StopIteration:
            log.append("stop")
    return repr(log)



SOURCES = {
    "iter_returns_non_iterator": "result = iter(NonIter())",
    "for_returns_non_iterator": "for x in NonIter(): pass",
    "no_next": "result = iter(NoNext())",
    "iter_none": "result = iter(IterNone())",
    "for_iter_none": "for x in IterNone(): pass",
    "not_iterable": "result = iter(Plain())",
    "for_not_iterable": "for x in 5: pass",
    "next_not_iterator": "result = next([1, 2])",
    "next_default": "result = next(iter([]), 'default')",
    "next_default_exhausted_twice": "it = iter([1])\nresult = (next(it, 'd'), next(it, 'd'), next(it, 'd'))",
    "generator_stopiteration": "def g():\n    raise StopIteration\n    yield\nresult = list(g())",
    "for_stops_at_first": "result = list(Revival())",
    "broken_iterator_revives": "r = Revival()\nresult = (list(r), next(r))",
    "iter_prefers_dunder_iter": "result = list(Both())",
    "sequence_index_error": "result = list(SeqIndexError())",
    "sequence_stop_iteration": "result = list(SeqStopIteration())",
    "sequence_lookup_error": "result = list(SeqLookupError())",
    "callable_not_callable": "result = iter(5, None)",
    "callable_sentinel_equality": "it = iter([1, 2.0, 3])\nresult = list(iter(lambda: next(it), 2))",
    "iter_of_iterator_is_self": "it = iter([1])\nresult = iter(it) is it and iter(iter(it)) is it",
    "for_calls_iter_once": "class Once:\n    count = 0\n    def __iter__(self):\n        Once.count += 1\n        return iter([1, 2])\nfor x in Once(): pass\nresult = Once.count",
    "list_iterator_mutation": "src = [1, 2, 3]\nout = []\nfor x in src:\n    out.append(x)\n    if x == 1: src.remove(x)\nresult = out",
    "dict_changed_size": "d = {1: 1}\nfor k in d: d[k + 1] = 1",
    "set_changed_size": "s = {1}\nfor k in s: s.add(k + 1)",
    "dict_keys_replaced_ok": "d = {1: 1, 2: 2}\nfor k in d: d[k] = 0\nresult = d",
    "iterator_type_names": "result = sorted({type(iter(x)).__name__ for x in ([], (), '', b'', {}, set(), range(1), bytearray())})",
    "length_hint": "it = iter([1, 2, 3])\nnext(it)\nresult = it.__length_hint__()",
    "hint_reversed_subclass": "log = []\nclass S:\n    def __len__(s):\n        log.append('len')\n        return 3\n"
                              "    def __getitem__(s, i): return i\nclass R(reversed): pass\nresult = (list(R(S())), log)",
    "hint_reversed_extend": "log = []\nclass S:\n    def __init__(s, fail=False): s.fail = fail\n    def __len__(s):\n        for _ in (): pass\n"
                            "        log.append('len')\n        if s.fail and len(log) > 1: raise LookupError\n        return 3\n"
                            "    def __getitem__(s, i): return i\nclass R(reversed): pass\nl = [9]\nl.extend(R(S()))\nn = list(log)\nlog.clear()\n"
                            "try:\n    l.extend(R(S(True)))\n    e = None\nexcept LookupError as x:\n    e = type(x).__name__\nresult = (l, n, e)",
    "bytes_reversed_subclass": "log = []\nclass S:\n    def __init__(s, items): s.items = items\n    def __len__(s):\n        for _ in (): pass\n"
                               "        log.append('len')\n        return len(s.items)\n    def __getitem__(s, i):\n        log.append(i)\n        return s.items[i]\n"
                               "class R(reversed): pass\nb = bytearray(b'z')\nr = bytes(R(S([65, 66])))\nb.extend(R(S([1, 2])))\nresult = (r, b, log)",
    "hint_sized": "log = []\nclass S:\n    def __len__(s):\n        for _ in (): pass\n        log.append('len')\n        return 3\n"
                  "    def __getitem__(s, i): return i\nit = iter(S())\nnext(it)\nr = reversed(S())\nnext(r)\nnext(r)\n"
                  "result = (it.__length_hint__(), r.__length_hint__(), log)",
    "hint_len_read": "log = []\nclass D:\n    def __init__(s, f, bad): s.f = f; s.bad = bad\n"
                     "    def __get__(s, obj, owner):\n        log.append('get ' + s.f.__name__)\n"
                     "        if s.bad: raise TypeError('read')\n        return s.f.__get__(obj, owner)\n"
                     "def __len__(self): return 2\ndef __length_hint__(self): return 5\n"
                     "def __iter__(self): return iter((1, 2))\n"
                     "X = type('X', (), {'__len__': D(__len__, True), '__length_hint__': D(__length_hint__, False), '__iter__': __iter__})\n"
                     "result = (list(X()), log)",
    "hint_hint_read": "log = []\nclass D:\n    def __init__(s, f, bad): s.f = f; s.bad = bad\n"
                     "    def __get__(s, obj, owner):\n        log.append('get ' + s.f.__name__)\n"
                     "        if s.bad: raise TypeError('read')\n        return s.f.__get__(obj, owner)\n"
                     "def __len__(self): return 2\ndef __length_hint__(self): return 5\n"
                     "def __iter__(self): return iter((1, 2))\n"
                      "X = type('X', (), {'__len__': D(__len__, True), '__length_hint__': D(__length_hint__, True), '__iter__': __iter__})\n"
                      "try:\n    list(X())\nexcept TypeError as e:\n    result = type(e).__name__",
    "hint_reversed_spent": "log = []\nclass S:\n    def __len__(s):\n        log.append('len')\n        return len(log) - 1\n"
                           "    def __getitem__(s, i): return i\nr = reversed(S())\ns = S()\nq = reversed(s)\nnext(q)\nlog.clear()\n"
                           "result = (r.__length_hint__(), q.__length_hint__(), log)",
    "next_dunder_direct": "it = iter('ab')\nresult = (it.__next__(), next(it))",
    "zip_strict": "result = list(zip([1, 2], [3], strict=True))",
    "map_multi": "result = list(map(pow, [2, 3], [3, 2, 9]))",
    "enumerate_start": "result = list(enumerate('ab', start=5))",
    "reversed_not_sequence": "result = reversed({1, 2})",
    "reversed_dunder": "class R:\n    def __reversed__(self): return iter('zy')\nresult = list(reversed(R()))",
    "exhausted_releases_source": "class Freed(dict):\n    def __del__(self): result.append('freed')\nresult = []\n"
                                 "for view in (dict.keys, lambda d: reversed(d.items())):\n"
                                 "    it = iter(view(Freed(k=1)))\n    result.append('made')\n"
                                 "    for _ in it: pass\n    result.append('exhausted')",
    "adapters_ask_again": "result = []\nfor make in (lambda r: map(abs, r), lambda r: filter(None, r), enumerate, zip):\n"
                          "    it = make(Revival())\n    result.append((list(it), next(it)))",
    "zip_ended_generator": "log = []\ndef gen(tag, *xs):\n    for x in xs:\n        log.append((tag, x)); yield x\n"
                           "z, m = zip(gen('a', 1, 2, 3), gen('e')), map(pow, gen('b', 1, 2, 3), gen('f'))\n"
                           "result = [list(z), list(z), list(m), list(m), log]",
    "hint_after_iter": "result = []\nclass S:\n    def __iter__(self): result.append('iter'); return iter((1, 2))\n"
                       "    def __len__(self): result.append('len'); return 2\n"
                       "l = list(S()); l.extend(S()); l += S(); [*S()]; sorted(S()); bytes(S())",
    "hint_sequence": "log = []\nclass U:\n    def __getitem__(s, i):\n        if i > 1: raise IndexError\n        return i\n"
                     "class S(U):\n    def __len__(s): log.append('len'); return 2\n"
                     "result = (list(reversed(S())), list(iter(S())), [*iter(U())], log)",
    "hint_fallback": "log = []\nclass S:\n    def __iter__(self): log.append('iter'); return iter((1, 2))\n"
                     "    def __len__(self): log.append('len'); raise TypeError\n"
                     "    def __length_hint__(self): log.append('hint'); return 5\nresult = (list(S()), log)",
    "hint_none": "class A:\n    def __iter__(self): return iter((1, 2))\n    def __length_hint__(self): return NotImplemented\n"
                 "class B(A):\n    def __length_hint__(self): raise TypeError\nresult = [list(A()), list(B())]",
    "hint_error": "class S:\n    def __iter__(self): return iter(())\n    def __length_hint__(self): raise ValueError('v')\n"
                  "result = list(S())",
    "hint_not_int": "class Hint:\n    def __iter__(self): return iter(())\n    def __length_hint__(self): return 'a'\n"
                    "result = list(Hint())",
    "hint_negative": "class Hint:\n    def __iter__(self): return iter(())\n    def __length_hint__(self): return -1\n"
                     "result = [*Hint()]",
    "len_error": "class S:\n    def __iter__(self): return iter(())\n    def __len__(self): return -1\nresult = bytes(S())",
    "no_hint_consumers": "result = []\nclass S:\n    def __iter__(self): result.append('iter'); return iter((1, 2))\n"
                         "    def __len__(self): result.append('len'); return 2\n"
                         "tuple(S()); set(S()); sum(S()); bytearray(S()); a, b = S()",
    "join_lists_iterator": "log = []\nclass It:\n    def __init__(self): self.items = ['a', 'b']\n"
                           "    def __iter__(self): log.append('iter'); return self\n"
                           "    def __next__(self):\n        if not self.items: raise StopIteration\n        return self.items.pop(0)\n"
                           "    def __len__(self): log.append('len'); return 2\nresult = ('-'.join(It()), log)",
    "join_bare_iterator": "class Bare:\n    def __next__(self): raise StopIteration\n"
                          "class Handing:\n    def __iter__(self): return Bare()\nresult = ''.join(Handing())",
    "pair_iterates_once": "log = []\nclass P:\n    def __iter__(self): log.append('iter'); return iter('ab')\nresult = (dict([P()]), log)",
    "subclass_iter": "log = []\nclass L(list):\n    def __iter__(self): log.append('iter'); return iter((7, 8))\n"
                     "    def __len__(self): log.append('len'); return 1\n"
                     "class T(tuple):\n    def __iter__(self): log.append('titer'); return iter((1,))\n"
                     "result = (list(L([1, 2])), sorted(L()), tuple(T((5,))), [*T()], log)",
    "int_subclass_iter": "log = []\nclass I(int):\n    def __iter__(self):\n        for _ in (): pass\n"
                         "        log.append('iter')\n        return iter([1, 2])\n"
                         "i = I(5)\nresult = (1 in i, 3 in i, list(i), sorted(i), (*i,), log)",
    "iterator_subclass_next": "log = []\nclass M(map):\n    def __next__(self): v = super().__next__(); log.append(v); return ('M', v)\n"
                              "class F(filter):\n    def __next__(self): return -super().__next__()\n"
                              "class Z(zip):\n    def __next__(self): return super().__next__()[::-1]\n"
                              "class E(enumerate):\n    def __next__(self): i, v = super().__next__(); return v * i\n"
                              "result = (list(M(abs, [-1, -2])), sorted(F(None, [0, 1, 2])), sum(Z([1], [2]), ()), list(E('ab')),\n"
                              "          [*M(abs, [1, 2])] and log, dict(Z([1], 'k')))",
    "adapter_getitem": "class S:\n    def __init__(s, n, flaky=False): s.n = n; s.failed = not flaky\n    def __getitem__(s, i):\n        for _ in range(2): pass\n        log.append(i)\n        if i == 1 and not s.failed:\n            s.failed = True\n            raise KeyError(i)\n        if i >= s.n: raise IndexError(i)\n        return i * 10\nclass B:\n    def __len__(s): return 2\n    def __getitem__(s, i): return 'b%d' % i\nlog = []\nz = zip(S(3, True), reversed(B()))\nfirst = next(z)\ntry: next(z)\nexcept KeyError as e: first = (first, 'KeyError')\nagain = zip(S(3), reversed(B()))\nresult = (first, list(z), list(z), dict(zip('ab', S(9))), list(enumerate(S(0))), list(again), list(again), log)",
    "adapter_nested": "log = []\ndef f(x):\n    for _ in range(2): pass\n    log.append(x)\n    if x == 4: raise ValueError(x)\n    return x * 10\nz = zip(zip('ab', map(f, [1, 4, 2])), 'uvw')\nfirst = next(z)\ntry: next(z)\nexcept ValueError: first = (first, 'ValueError')\ne = enumerate(zip(map(f, [3, 5]), 'xy'))\nresult = (first, list(z), list(e), list(enumerate(enumerate(map(f, [6])))), log)",
    "adapter_delegate": "log = []\nclass K:\n    def __str__(s):\n        for _ in range(2): pass\n        log.append('str')\n        return 'k'\ndef f(x):\n    for _ in range(2): pass\n    log.append(x)\n    if x == 3: raise StopIteration(33)\n    if x == 4: raise ValueError(x)\n    return x * 10\ndef gen(it):\n    r = yield from it\n    yield ('ret', r)\ndef run(it):\n    try: return list(gen(it))\n    except ValueError: return 'ValueError'\nresult = (run(zip(map(f, [1, 3]), 'ab')), run(enumerate(map(str, [K()]))), run(zip('a', map(f, [4]))), run(map(len, map(str, [K(), K()]))), log)",
    "next_generator_value": "def gen(*items, ret=None):\n    for item in items:\n        for _ in range(2): pass\n        yield item\n    return ret\ndef stop(it, *default):\n    try: return next(it, *default)\n    except StopIteration as e: return ('StopIteration', e.args)\nz = zip(gen(1, ret=5), 'xy')\nm = map(abs, gen(-1, ret=7))\ne = enumerate(gen(1, ret=8))\nf = filter(None, gen(0, 1, ret=4))\nresult = (stop(z), stop(z), stop(z), stop(m), stop(m), stop(e), stop(e), stop(e, 'd'), stop(f), stop(f))",
    "released_items_finalized": ("log = []\nclass Item:\n    def __init__(self, i): self.i = i\n"
                                 "    def __del__(self):\n        for _ in (): pass\n        log.append(self.i)\n"
                                 "def items(n):\n    for i in range(n): yield Item(i)\n"
                                 "def run():\n    for pair in zip(items(2), range(2)): pass\n"
                                 "    for n in map(lambda item: item.i, items(2)): pass\n    pair = None\n    log.append('a')\n    return log\n"
                                 "result = run()"),
    "zip_strict_generators": "log = []\ndef gen(name, *items, ret=None):\n    for item in items:\n        for _ in range(2): pass\n        log.append((name, item))\n        yield item\n    log.append(name)\n    return ret\ndef run(f):\n    try: return f()\n    except (ValueError, StopIteration) as e: return (type(e).__name__, str(e))\nz = zip(gen('a', 1, ret=5), gen('b', 3), strict=True)\nresult = (run(lambda: list(zip(gen('a', 1, 2), gen('b', 3), strict=True))),\n          run(lambda: list(zip(gen('a', 1), gen('b', 3, 4), strict=True))),\n          run(lambda: list(map(pow, gen('a', 2), [1], gen('c', 1), strict=True))),\n          run(lambda: next(z)), run(lambda: next(z)), log)",
    "metaclass_getitem": "log = []\nclass Meta(type):\n    def __len__(cls): return 2\n    def __getitem__(cls, i):\n"
                         "        log.append(i)\n        if i == cls.bad: raise LookupError(i)\n        if i > 1: raise IndexError(i)\n"
                         "        return i * 10\nclass S(metaclass=Meta): bad = -1\nclass B(metaclass=Meta): bad = 0\n"
                         "def bad():\n    try: return list(B)\n    except LookupError: return 'LookupError'\n"
                         "result = (list(S), list(reversed(S)), sum(S), sorted(S, reverse=True), bad(), log)",
    "next_method": "log = []\ndef sq(x): log.append(x); return x * x\nclass M(map):\n    def __next__(self): return super().__next__()\n"
                   "m, w = map(sq, [1, 2]), map(sq, [3]).__next__\n"
                   "try: map.__next__(filter(None, [1]))\nexcept TypeError as e: kind = 'TypeError'\n"
                   "result = (m.__next__(), map.__next__(m), w(), next(M(sq, [3]).__iter__()) - 6, kind, log + list(M(sq, [2, 3])))",
}


TYPES = {name: value for name, value in list(globals().items()) if isinstance(value, type) and name[0].isupper()}


def generated(p):
    return run(p["kind"], p["n"])


def outcome(p):
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


check_programs(outcome)
