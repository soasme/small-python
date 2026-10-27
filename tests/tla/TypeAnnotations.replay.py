# Replays TypeAnnotations.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
class C:
    def __class_getitem__(cls, item): return ("cgi", item)
class G(list): pass
TERMS = ["int", "str", "None", "bool"]
SEQS = [(a, b) for a in TERMS for b in TERMS] + [(a, b, c) for a in TERMS for b in TERMS for c in TERMS]
VALUES = [1, "", None, True]


def union_of(terms):
    try:
        u = eval(" | ".join(terms))
    except TypeError as error:
        return "TypeError: %s" % error
    args = getattr(u, "__args__", None)
    names = "-" if args is None else [a.__name__ for a in args]
    return repr((repr(u), names, [isinstance(v, u) for v in VALUES]))

SOURCES = {
    "list_int": 'a = list[int]\nresult = (repr(a), a.__origin__ is list, a.__args__, a.__parameters__, type(a).__name__)',
    "dict_args": 'a = dict[str, list[int]]\nresult = (repr(a), a.__args__)',
    "tuple_ellipsis": 'result = (repr(tuple[int, ...]), tuple[()].__args__, repr(tuple[()]))',
    "call_origin": "result = list[int]('ab')",
    "no_runtime_check": 'result = list[str]([1, 2])',
    "isinstance_fails": 'result = isinstance([], list[int])',
    "issubclass_fails": 'result = issubclass(list, list[int])',
    "eq": 'result = (list[int] == list[int], list[int] == list[str], list[int] == list, hash(list[int]) == hash(list[int]))',
    "unpacked": 'a = tuple[int]\nu = [*a][0]\nresult = (repr(u), u.__unpacked__, a.__unpacked__, repr(tuple[*tuple[int, ...]]))',
    "unpack_non_tuple": 'result = [*list[int]]',
    "type_of_origin": 'result = (type[int].__origin__ is type, repr(type[int]))',
    "getattr_forward": 'result = (list[int].append is list.append, list[int].__name__, list[int].__qualname__, list[int].__module__)',
    "dir_like": 'result = list[int].__mro__ == list.__mro__',
    "class_getitem": 'result = C[int]',
    "subclass_alias": "a = G[int]\nresult = (repr(a).endswith('G[int]'), a.__origin__ is G)",
    "nested_param": 'def f[T](): return T\nT = f()\na = list[T]\nresult = (a.__parameters__, repr(a[int]), repr(dict[str, T][int]))',
    "too_many_args": 'def f[T](): return T\nT = f()\nresult = list[T][int, str]',
    "not_generic": 'result = list[int][int]',
    "subscript_int": 'result = int[str]',
    "union_or": 'u = int | str\nresult = (repr(u), type(u).__name__, u.__args__)',
    "union_dedup": 'result = (repr(int | int), int | int is int, repr(int | str | int), (int | str) == (str | int))',
    "union_none": 'result = (repr(int | None), repr(None | int), (int | None).__args__)',
    "union_isinstance": 'result = (isinstance(1, int | str), isinstance(1.0, int | str), issubclass(bool, int | str), isinstance(None, int | None))',
    "union_generic_isinstance": 'result = isinstance([], list[int] | int)',
    "union_nested": 'result = (repr((int | str) | float), (int | (str | float)).__args__)',
    "union_bad": 'result = int | 1',
    "union_bad_left": 'result = 1 | int',
    "union_hash": 'result = (hash(int | str) == hash(str | int), len({int | str, str | int}))',
    "union_generic_alias": 'result = repr(list[int] | None)',
    "union_param": 'def f[T](): return T\nT = f()\nu = list[T] | None\nresult = (u.__parameters__, repr(u[int]))',
    "union_getitem_noparams": 'result = (int | str)[int]',
    "union_origin": 'result = (int | str).__origin__',
    "union_subclass": 'class X(int | str): pass',
    "union_eq_order": 'result = (int | str | float) == (float | str | int)',
    "union_call": 'result = (int | str)()',
    "ga_instancecheck_inner": 'result = isinstance(list[int], type)',
    "ga_repr_nested": 'result = repr(list[list[dict[str, ...]]])',
    "ga_repr_callable_like": 'result = repr(dict[int, ...])',
    "ga_star_star": 'result = repr(tuple[*tuple[int, str]])',
    "ga_args_tuple_single": 'result = list[(int,)].__args__',
    "ga_args_list_param": 'result = repr(list[[int, str]])',
    "ga_mro_entries": 'class D(list[int]): pass\nresult = (D.__bases__, D.__orig_bases__ == (list[int],))',
    "ga_setattr": 'a = list[int]\na.x = 1',
    "ga_copy_attr_ok": 'result = list[int].__class__.__name__'
}


TYPES = {name: value for name, value in list(globals().items()) if isinstance(value, type) and name[0].isupper()}

def generated(p):
    return union_of(p["terms"])


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
