# Replays ExceptionGroups.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's. The
# generated groups derive by a Python method, and split as a method and
# unbound, which agree.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
class MyEG(ExceptionGroup):
    def derive(self, excs): return MyEG(self.message + "!", excs)
class Looping(ExceptionGroup):
    """Derives as the default does, by a Python derive that loops."""
    def derive(self, excs):
        for _ in range(2): pass
        return ExceptionGroup(self.message, excs)
ITEMS = ["V", "T", "GVT", "GT"]
SHAPES = [(a,) for a in ITEMS] + [(a, b) for a in ITEMS for b in ITEMS] + [(a, b, c) for a in ITEMS for b in ITEMS for c in ITEMS]


def build(item):
    if item == "V": return ValueError(1)
    if item == "T": return TypeError(2)
    if item == "GVT": return Looping("inner", [ValueError(3), TypeError(4)])
    return Looping("only", [TypeError(5)])


def shape(e):
    if e is None: return "None"
    if isinstance(e, BaseExceptionGroup): return "G(" + ",".join(shape(x) for x in e.exceptions) + ")"
    return type(e).__name__[0]


def inner(e):
    for _ in range(2): pass
    return isinstance(e, ExceptionGroup) and e.message == "inner"


def grouped(op, items):
    g = Looping("top", [build(i) for i in items])
    if op == "str": return str(g)
    # As a method and unbound from the class: one outcome.
    method, cond = {"split_value": ("split", ValueError), "split_type": ("split", TypeError),
                    "subgroup_value": ("subgroup", ValueError), "split_pred": ("split", inner)}[op]
    outcomes = {parts(getattr(g, method)(cond)), parts(getattr(ExceptionGroup, method)(g, cond))}
    return outcomes.pop() if len(outcomes) == 1 else "mismatch"


def parts(result):
    return " ".join(map(shape, result)) if type(result) is tuple else shape(result)

SOURCES = {
    "base_to_exception": "result = (type(BaseExceptionGroup('m', [ValueError()])).__name__, type(BaseExceptionGroup('m', [KeyboardInterrupt()])).__name__)",
    "eg_rejects_base": "result = ExceptionGroup('m', [KeyboardInterrupt()])",
    "empty": "result = ExceptionGroup('m', [])",
    "not_sequence": "result = ExceptionGroup('m', {ValueError()})",
    "not_exception_item": "result = ExceptionGroup('m', [1])",
    "message_type": 'result = ExceptionGroup(1, [ValueError()])',
    "arity": "result = ExceptionGroup('m')",
    "attributes": "g = ExceptionGroup('m', [ValueError(1)])\nresult = (g.message, type(g.exceptions).__name__, g.args[0], type(g.args[1]).__name__)",
    "readonly": "g = ExceptionGroup('m', [ValueError(1)])\ng.message = 'x'",
    "repr": "result = repr(ExceptionGroup('m', [ValueError(1), TypeError(2)]))",
    "custom_repr_saved": "log = []\nclass S:\n    def __init__(s, r): s.r = r\n    def __getitem__(s, i):\n        for _ in (): pass\n"
                         "        log.append(i)\n        if i: raise IndexError\n        return ValueError()\n"
                         "    def __repr__(s):\n        for _ in (): pass\n        log.append('repr')\n        return s.r\n"
                         "seq = S('S')\ng = ExceptionGroup('m', seq)\nseq.r = 'T'\nresult = (repr(g), log)",
    "split_truth": "log = []\nclass T:\n    def __init__(s, v): s.v = v\n    def __bool__(s):\n        for _ in (): pass\n        log.append(s.v)\n        return s.v\n"
                   "g = ExceptionGroup('m', [ValueError(1), TypeError(2)])\nm, r = g.split(lambda e: T(isinstance(e, TypeError)))\n"
                   "try: g.split(lambda e: T(1))\nexcept TypeError as e: err = str(e)\nresult = (len(m.exceptions), len(r.exceptions), log[:2], err)",
    "custom_repr_not_str": "class S:\n    def __getitem__(s, i): return ValueError()\n    def __repr__(s):\n        for _ in (): pass\n"
                           "        return 1\nresult = ExceptionGroup('m', S())",
    "derive_custom": "g = MyEG('m', [ValueError(1), TypeError(2)])\nm, r = g.split(ValueError)\nresult = (type(m).__name__, m.message, r.message)",
    "derive_default_drops_subclass": "class E(ExceptionGroup): pass\nm, r = E('m', [ValueError(), TypeError()]).split(ValueError)\nresult = (type(m).__name__, type(r).__name__)",
    "split_copies_metadata": "g = ExceptionGroup('m', [ValueError(1), TypeError(2)])\ng.add_note('n')\ng.__cause__ = KeyError()\nm, r = g.split(ValueError)\nresult = (m.__notes__, type(m.__cause__).__name__, m.__notes__ is g.__notes__)",
    "split_tuple_types": "g = ExceptionGroup('m', [ValueError(1), TypeError(2), KeyError(3)])\nm, r = g.split((ValueError, KeyError))\nresult = (len(m.exceptions), len(r.exceptions))",
    "split_all_returns_self": "g = ExceptionGroup('m', [ValueError(1)])\nm, r = g.split(ValueError)\nresult = (m is g, r)",
    "split_group_type": "g = ExceptionGroup('m', [ValueError(1)])\nm, r = g.split(ExceptionGroup)\nresult = (m is g, r)",
    "split_bad_arg": "ExceptionGroup('m', [ValueError()]).split(1)",
    "subgroup_none": "result = ExceptionGroup('m', [ValueError()]).subgroup(TypeError)",
    "str_count": "result = (str(ExceptionGroup('m', [ValueError()])), str(ExceptionGroup('m', [ValueError(), ValueError()])))",
    "except_star_unwrap": "try:\n    raise ExceptionGroup('m', [ValueError(1)])\nexcept* ValueError as eg:\n    result = (type(eg).__name__, len(eg.exceptions))",
    "nested_traceback_kept": "result = ExceptionGroup('m', [ValueError()]).exceptions[0].__traceback__",
    "generic_alias": 'result = repr(ExceptionGroup[ValueError])',
    "list_copied": "l = [ValueError()]\ng = ExceptionGroup('m', l)\nl.append(TypeError())\nresult = len(g.exceptions)"
}


TYPES = {name: value for name, value in list(globals().items()) if isinstance(value, type) and name[0].isupper()}


def generated(p):
    return grouped(p["op"], p["items"])


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
