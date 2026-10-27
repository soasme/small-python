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
    "next_dunder_direct": "it = iter('ab')\nresult = (it.__next__(), next(it))",
    "zip_strict": "result = list(zip([1, 2], [3], strict=True))",
    "map_multi": "result = list(map(pow, [2, 3], [3, 2, 9]))",
    "enumerate_start": "result = list(enumerate('ab', start=5))",
    "reversed_not_sequence": "result = reversed({1, 2})",
    "reversed_dunder": "class R:\n    def __reversed__(self): return iter('zy')\nresult = list(reversed(R()))"
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
