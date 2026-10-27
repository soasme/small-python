# Replays ExceptionGroups.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
class MyEG(ExceptionGroup):
    def derive(self, excs): return MyEG(self.message + "!", excs)
ITEMS = ["V", "T", "GVT", "GT"]
SHAPES = [(a,) for a in ITEMS] + [(a, b) for a in ITEMS for b in ITEMS] + [(a, b, c) for a in ITEMS for b in ITEMS for c in ITEMS]


def build(item):
    if item == "V": return ValueError(1)
    if item == "T": return TypeError(2)
    if item == "GVT": return ExceptionGroup("inner", [ValueError(3), TypeError(4)])
    return ExceptionGroup("only", [TypeError(5)])


def shape(e):
    if e is None: return "None"
    if isinstance(e, BaseExceptionGroup): return "G(" + ",".join(shape(x) for x in e.exceptions) + ")"
    return type(e).__name__[0]


def grouped(op, items):
    g = ExceptionGroup("top", [build(i) for i in items])
    if op == "split_value": m, r = g.split(ValueError); return shape(m) + " " + shape(r)
    if op == "split_type": m, r = g.split(TypeError); return shape(m) + " " + shape(r)
    if op == "subgroup_value": return shape(g.subgroup(ValueError))
    if op == "split_pred": m, r = g.split(lambda e: isinstance(e, ExceptionGroup) and e.message == "inner"); return shape(m) + " " + shape(r)
    if op == "str": return str(g)

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
