# Replays Atoms.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()

SOURCES = {
    "true_const": "result = (True, type(True).__name__)",
    "none_const": "result = None",
    "ellipsis_const": "result = (..., ... is Ellipsis, type(...).__name__)",
    "assign_false": "False = 123",
    "assign_none": "None = 1",
    "assign_true_aug": "True += 1",
    "attr_none": "x.None = 1",
    "attr_true_read": "result = x.True",
    "assign_ellipsis": "... = 1",
    "del_none": "del None",
    "for_true": "for True in []: pass",
    "param_none": "def f(None): pass",
    "kwarg_true": "f(True=1)",
    "import_as_none": "import os as None",
    "assign_debug": "__debug__ = 1",
    "ellipsis_name": "Ellipsis = 3\nresult = (Ellipsis, ... is not Ellipsis)",
    "name_bound": "x = [1]\nresult = x",
    "name_unbound": "result = undefined_name",
    "name_deleted": "x = 1\ndel x\nresult = x",
    "literal_int": "result = type(10).__name__",
    "literal_float": "result = (type(1.5).__name__, 1e400, 0.1 + 0.2)",
    "literal_imag": "result = (type(2j).__name__, 2j.real, 2j.imag)",
    "literal_str": "result = type('a').__name__",
    "literal_bytes": "result = type(b'a').__name__",
    "literal_fstring": "result = type(f'{1}').__name__",
    "literal_tstring": "result = type(t'{1}').__name__",
    "negative_not_literal": "result = (-2 ** 2, (-2) ** 2)",
    "complex_not_literal": "result = (3+4.2j, type(3+4.2j).__name__)",
    "same_value": "x = 123456789\ny = 123456789\nresult = (x == y, 7 == 7)",
    "str_equal": "result = 'ab' == 'a' 'b'",
    "tstring_distinct": "def f():\n    return t'{1}'\nresult = f() is f()",
    "tstring_values_shared": "v = []\ndef f():\n    return t'{v}'\nresult = (f().interpolations[0].value is f().interpolations[0].value, f().values[0] is v)",
    "tstring_mutable_value": "v = []\nt = t'{v}'\nv.append(1)\nresult = t.values",
    "literal_immutable_int": "x = 5\ntry:\n    x.real = 1\nexcept AttributeError:\n    result = 'immutable'",
    "literal_immutable_str": "s = 'abc'\ntry:\n    s[0] = 'x'\nexcept TypeError as e:\n    result = str(e)",
    "literal_immutable_bytes": "s = b'abc'\ntry:\n    s[0] = 1\nexcept TypeError as e:\n    result = str(e)",
    "float_approx": "result = 0.1 == 0.1000000000000000055511151231257827",
    "huge_imag": "result = 1e400j",
    "small_identity_unspecified": "x = 7\ny = 7\nresult = (x is y) in (True, False) and x == y",
    "large_identity_unspecified": "x = 123456789\ny = 123456789\nresult = (x is y) in (True, False) and x == y",
    "repeated_evaluation_equal": "def f():\n    return (1.5, 'a', b'b', 2j)\nresult = f() == f()",
    "group_value": "result = (1 + 2) * 3",
    "empty_tuple": "result = ()",
    "yield_atom_outside": "x = (yield)"
}


def outcome(p):
    namespace = {}
    try:
        exec(compile(SOURCES[p["case"]], "<case>", "exec"), namespace)
        return repr(namespace.get("result"))
    except SyntaxError as error:
        return "%s: %s" % (type(error).__name__, error.msg)
    except Exception as error:
        return "%s: %s" % (type(error).__name__, error)


check_programs(outcome)
