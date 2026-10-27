# Replays Displays.tla: each case builds the spec's display (or runs one of
# the spec's sources), logging every item as it is evaluated, and compares
# the result and the log with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SEQUENCE_ITEMS = {"plain": "t({i})", "true": "t(True)", "star": "*t([{i}, {i} + 10])", "empty": "*t([])",
                  "bad": "*t({i})"}
DICT_ITEMS = {"pair": "t({i}): t({i} + 100)", "true_pair": "t(True): t({i} + 100)", "merge": "**t({{1: {i} + 200}})",
              "bad": "**t({i})"}
OPEN = {"list": "[", "tuple": "(", "set": "{", "dict": "{"}
CLOSE = {"list": "]", "tuple": ",)", "set": "}", "dict": "}"}
SOURCES = {
    "paren_same": "x = [1]\nresult = (x) is x",
    "paren_yield": "def g():\n    v = (yield 1)\n    yield v\nit = g()\nnext(it)\nresult = it.send(5)",
    "empty": "result = ((), [], {}, type({}).__name__)",
    "tuple_needs_comma": "result = ((1,)[0], type((1)).__name__)",
    "trailing_comma": "result = ([1, 2,], {1,}, {1: 2,})",
    "nested": "result = [t(1), [t(2), (t(3), {t(4)})], {t(5): [t(6)]}]",
    "dict_unhashable": "{[]: 1}",
    "set_unhashable": "{[1]}",
    "dict_late_unhashable": "{t(1): t(2), t([]): t(3)}",
    "dstar_keys_protocol": "class M:\n    def keys(self): return ['k']\n    def __getitem__(self, k): return k.upper()\n"
                           "result = {**M()}",
    "dstar_bad_keys": "class M:\n    def keys(self): return 5\n    def __getitem__(self, k): return k\n{**M()}",
    "star_generator_error": "def g():\n    yield t(1)\n    raise ValueError('mid')\n[*g()]",
    "star_bare": "*a",
    "dstar_in_list": "[**{}]",
    "dstar_in_set": "{**{}, 1}",
    "list_identity": "result = [] is not []",
}


def source(p):
    if "case" in p:
        return SOURCES[p["case"]]
    kind, items = p["kind"], p["items"]
    forms = DICT_ITEMS if kind == "dict" else SEQUENCE_ITEMS
    parts = [forms[item].format(i=i) for i, item in enumerate(items, 1)]
    if not parts:
        return "result = " + {"list": "[]", "tuple": "()", "set": "set()", "dict": "{}"}[kind]
    return "result = " + OPEN[kind] + ", ".join(parts) + CLOSE[kind]


def outcome(p):
    log = []

    def t(value):
        log.append(repr(value))
        return value

    namespace = {"t": t}
    try:
        exec(compile(source(p), "<display>", "exec"), namespace)
    except Exception as error:
        return ("%s: %s" % (type(error).__name__, str(error).split(" (")[0]), (), tuple(log))
    result = namespace.get("result")
    if "case" in p:
        if p["case"] == "tuple_needs_comma":
            result = "(%r, %s)" % result
            return ("ok", result, tuple(log))
        return ("ok", repr(result), tuple(log))
    if type(result) is set:
        value = frozenset(repr(x) for x in result)
    elif type(result) is dict:
        value = tuple((repr(k), repr(v)) for k, v in result.items())
    else:
        value = tuple(repr(x) for x in result)
    return ("ok", value, tuple(log))


check_programs(outcome)
