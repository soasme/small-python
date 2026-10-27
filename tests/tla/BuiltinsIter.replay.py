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
    "filter_none": "result = list(filter(None, [0, 1, '', 'a', None, []]))",
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
    "sort_gt_reflected": 'class G:\n    def __init__(self, v): self.v = v\n    def __gt__(self, o): return self.v > o.v\nresult = [x.v for x in sorted([G(2), G(1)])]',
    "len_negative": 'result = len(NegLen())',
    "len_big": 'result = len(BigLen())',
    "len_float": 'result = len(FloatLen())',
    "len_unsized": 'result = len(5)',
    "sum_iter": 'result = sum(x * x for x in range(4))',
    "aiter_sync": 'result = aiter([])',
    "slice_builtin": 'result = ([0, 1, 2, 3][slice(1, None, 2)], slice(3).indices(10), repr(slice(1, 2)))',
    "range_iter_type": 'result = type(iter(range(3))).__name__'
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
