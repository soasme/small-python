# Replays Sentinels.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SOURCES = {
    "repr_default": "M = sentinel('MISSING')\nresult = repr(M)",
    "repr_custom": "M = sentinel('MISSING', repr='<MISSING>')\nresult = repr(M)",
    "str_form": "M = sentinel('MISSING')\nresult = str(M)",
    "name_attr": "M = sentinel('MISSING')\nresult = M.__name__",
    "module_attr": "M = sentinel('MISSING')\nresult = M.__module__",
    "module_writable": "M = sentinel('MISSING')\nM.__module__ = 'elsewhere'\nresult = M.__module__",
    "truthy": "result = bool(sentinel('X'))",
    "unique": "result = sentinel('X') is sentinel('X')",
    "equal_self": "M = sentinel('X')\nresult = (M == M, M != M)",
    "not_equal_other": "result = sentinel('X') == sentinel('X')",
    "hashable": "M = sentinel('X')\nresult = {M: 1}[M]",
    "name_not_str": "sentinel(1)",
    "repr_not_str": "sentinel('X', repr=1)",
    "repr_positional": "sentinel('X', 'Y')",
    "no_args": "sentinel()",
    "no_subclass": "class S(sentinel): pass",
    "type_name": "result = type(sentinel('X')).__name__",
    "type_is_sentinel": "result = type(sentinel('X')) is sentinel",
    "union": "M = sentinel('M')\nresult = repr(int | M)",
    "union_left": "M = sentinel('M')\nresult = repr(M | None)",
    "annotation": "M = sentinel('MISSING')\ndef f(default: int | M = M): return default\nresult = (f() is M, f.__annotations__['default'] == (int | M))",
    "is_compare": "M = sentinel('M')\nx = M\nresult = x is M",
    "nonidentifier_name": "result = repr(sentinel('not an identifier'))",
    "name_readonly": "M = sentinel('M')\nM.__name__ = 'N'",
    "new_attr": "M = sentinel('M')\nM.other = 1",
    "ordering": "sentinel('A') < sentinel('B')",
    "builtin": "import builtins\nresult = builtins.sentinel is sentinel",
    "repr_none": "result = repr(sentinel('X', repr=None))",
    "repr_str_form": "M = sentinel('X', repr='<r>')\nresult = (str(M), f'{M}', M.__name__)",
    "unknown_keyword": "sentinel('X', foo=1)",
    "too_many": "sentinel('X', 'Y', 'Z')",
    "keyword_too_many": "sentinel('X', repr='r', foo=2)",
    "name_keyword": "sentinel(name='X')",
    "module_any": "M = sentinel('X')\nM.__module__ = 3\nresult = M.__module__",
    "module_delete": "M = sentinel('X')\ndel M.__module__\nresult = hasattr(M, '__module__')",
    "module_delete_twice": "M = sentinel('X')\ndel M.__module__\ndel M.__module__",
    "name_delete": "M = sentinel('X')\ndel M.__name__",
    "module_global": "ns = {'__name__': 'mymod'}\nexec('M = sentinel(\\'X\\')', ns)\nresult = ns['M'].__module__",
    "module_function": "def make():\n    return sentinel('X')\nmake.__module__ = 'fmod'\nresult = make().__module__",
    "reduce": "result = sentinel('X', repr='r').__reduce__()",
    "copy_self": "M = sentinel('X')\nresult = (M.__copy__() is M, M.__deepcopy__({}) is M)",
    "union_repr": "result = repr(sentinel('X', repr='<r>') | int)",
    "type_module": "result = (sentinel.__module__, sentinel.__qualname__)"
}


def outcome(p):
    namespace = {}
    try:
        exec(compile(SOURCES[p["case"]], "<case>", "exec"), namespace)
        return repr(namespace.get("result"))
    except Exception as error:
        return "%s: %s" % (type(error).__name__, error)


check_programs(outcome)
