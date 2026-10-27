# Replays Constants.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
class A:
    def __eq__(self, other): return NotImplemented
class B:
    def __eq__(self, other): return "B.eq"
NAMES = ["None", "True", "False", "__debug__", "Ellipsis", "NotImplemented", "x"]
CONTEXTS = {
    "assign": "{} = 1",
    "augassign": "{} += 1",
    "annotated": "{}: int = 1",
    "delete": "del {}",
    "for": "for {} in []: pass",
    "with": "with c as {}: pass",
    "param": "def f({}): pass",
    "keyword": "f({}=1)",
    "walrus": "({} := 1)",
    "import_as": "import m as {}",
    "def": "def {}(): pass",
    "class": "class {}: pass",
    "attribute": "o.{} = 1",
    "lambda": "lambda {}: 0",
    "global": "def g():\n    global {}",
    "except_as": "try: pass\nexcept E as {}: pass",
    "starred": "a, *{} = ()",
    "comprehension": "[0 for {} in ()]",
}


def target(name, context):
    try:
        compile(CONTEXTS[context].format(name), "<case>", "exec")
    except SyntaxError as error:
        return "SyntaxError: %s" % error.msg
    return "ok"

SOURCES = {
    "assign_none": "exec('None = 1')",
    "assign_true": "exec('True = 1')",
    "assign_false_attr": "exec('x.False = 1')",
    "assign_debug": "exec('__debug__ = 1')",
    "del_debug": "exec('del __debug__')",
    "debug_param": "exec('def f(__debug__): pass')",
    "debug_kw": "exec('f(__debug__=1)')",
    "none_kw": "exec('f(None=1)')",
    "debug_value": 'result = (__debug__, type(__debug__).__name__)',
    "assert_runs": "try:\n    assert False, 'm'\nexcept AssertionError as e:\n    result = e.args",
    "none_type": 'result = (type(None)(), type(None).__name__, type(None)() is None)',
    "none_type_args": 'result = type(None)(1)',
    "ni_type": 'result = (type(NotImplemented)() is NotImplemented, repr(NotImplemented), type(NotImplemented).__name__)',
    "ni_bool": 'result = bool(NotImplemented)',
    "ni_reflected": 'result = A() == B()',
    "ni_both": 'result = (A() == A(), A() != A())',
    "ni_identity_fallback": 'a = A()\nresult = (a == a, a != a)',
    "ni_ordering": 'result = A() < A()',
    "ellipsis": 'result = (Ellipsis is ..., repr(...), type(...).__name__, type(...)() is ..., str(Ellipsis))',
    "ellipsis_bool": 'result = bool(...)',
    "true_false": 'result = (True + True, False * 3, repr(True), True is not False, type(True).__mro__[1].__name__)',
    "bool_subclass": 'class X(bool): pass',
    "builtins_name": 'result = (None.__class__.__name__, NotImplemented.__class__.__name__, Ellipsis.__class__.__name__)',
    "hash_singletons": 'result = (hash(None) == hash(None), hash(...) == hash(...), hash(True) == 1)',
    "keyword_shadow": 'def f(): return None\nresult = f() is None',
    "builtins_dict": "import builtins\nresult = (builtins.Ellipsis is ..., builtins.NotImplemented is NotImplemented, 'None' in dir(builtins), builtins.__dict__['__debug__'])",
    "assign_ellipsis_name": 'Ellipsis = 1\nresult = (Ellipsis, ... is not Ellipsis)',
    "assign_ni_name": 'NotImplemented = 2\nresult = NotImplemented',
    "debug_walrus": "exec('(__debug__ := 1)')",
    "true_walrus": "exec('(True := 1)')",
    "none_import_as": "exec('import x as None')",
    "debug_import_as": "exec('import x as __debug__')",
    "debug_for": "exec('for __debug__ in []: pass')",
    "debug_class": "exec('class __debug__: pass')",
    "debug_attr_ok": 'class N: pass\nn = N()\nn.__debug__ = 1\nresult = n.__debug__',
    "debug_global_ok_getattr": "result = __builtins__['__debug__'] if isinstance(__builtins__, dict) else __builtins__.__debug__"
}


TYPES = {name: value for name, value in list(globals().items()) if isinstance(value, type) and name[0].isupper()}


def generated(p):
    return target(p["name"], p["context"])


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
