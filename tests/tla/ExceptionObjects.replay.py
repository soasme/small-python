# Replays ExceptionObjects.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
class Sub(Exception):
    pass


VALUES = {"s": "a", "i": 1, "n": None}
CLASSES = {"Exception": Exception, "KeyError": KeyError, "Sub": Sub}


def shown(op, cls, args):
    e = CLASSES[cls](*[VALUES[a] for a in args])
    if op == "str": return repr(str(e))
    if op == "repr": return repr(repr(e))
    if op == "args": return repr(e.args)
    if op == "base_str": return repr(BaseException.__str__(e))
class NoSuper(Exception):
    def __init__(self, x): self.x = x
class MyStr(Exception):
    def __str__(self): return "custom"
class Two(Exception):
    def __init__(self, a, b): super().__init__(a, b)
class Key(KeyError):
    def __str__(self): return "<" + super().__str__() + ">"
class Quiet(ValueError):
    def __repr__(self): return "Quiet!"

SOURCES = {
    "args_set_by_new": 'e = NoSuper(5)\nresult = (e.args, e.x, str(e))',
    "args_assign_tuple": 'e = Exception()\ne.args = [1, 2]\nresult = (e.args, type(e.args).__name__)',
    "args_assign_bad": 'e = Exception()\ne.args = 1',
    "with_traceback_self": 'e = ValueError()\nresult = (e.with_traceback(None) is e, e.__traceback__)',
    "traceback_bad": 'ValueError().__traceback__ = 1',
    "with_traceback_bad": 'ValueError().with_traceback(1)',
    "add_note": "e = ValueError('v')\ne.add_note('one')\ne.add_note('two')\nresult = (e.__notes__, str(e))",
    "add_note_bad": 'ValueError().add_note(1)',
    "notes_absent": "result = hasattr(ValueError(), '__notes__')",
    "notes_replaced_bad": "e = ValueError()\ne.__notes__ = 1\ne.add_note('x')",
    "context_defaults": 'e = ValueError()\nresult = (e.__context__, e.__cause__, e.__suppress_context__)',
    "cause_assign_bad": 'ValueError().__cause__ = 1',
    "context_assign_bad": "ValueError().__context__ = 'x'",
    "cause_sets_suppress": 'e = ValueError()\ne.__cause__ = KeyError()\nresult = e.__suppress_context__',
    "custom_str": 'result = (str(MyStr(1)), repr(MyStr(1)), MyStr(1).args)',
    "kwargs_refused": 'result = Exception(x=1)',
    "kwargs_subclass_init": 'class K(Exception):\n    def __init__(self, x=None): super().__init__(x)\nresult = K(x=3).args',
    "reduce": 'e = Two(1, 2)\nresult = (e.__reduce__()[0] is Two, e.__reduce__()[1])',
    "reduce_dict": 'e = ValueError(1)\ne.extra = 2\nresult = e.__reduce__()[2]',
    "setstate": "e = ValueError()\ne.__setstate__({'k': 1})\nresult = e.k",
    "setstate_bad": 'ValueError().__setstate__(1)',
    "exception_dict": 'e = ValueError()\ne.anything = 1\nresult = vars(e)',
    "inherit_init_args": "class P(KeyError):\n    pass\nresult = (str(P('k')), P('k', 2).args)",
    "base_new_args": 'e = BaseException.__new__(ValueError, 1, 2)\nresult = e.args',
    "str_of_class_instance": "result = str(Exception(Exception('inner')))",
    "repr_trailing_comma": 'result = (repr(ValueError((1,))), repr(ValueError(1, )))',
    "equality_identity": 'a = ValueError(1)\nresult = (a == ValueError(1), a == a)',
    "hashable": 'result = isinstance(hash(ValueError()), int)',
    "systemexit_code": 'result = (SystemExit().code, SystemExit(1).code, SystemExit(1, 2).code)',
    "stopiteration_value": 'result = (StopIteration().value, StopIteration(1, 2).value)',
    "keyerror_str_tuple": 'result = (str(KeyError(1, 2)), str(KeyError(())))',
    "super_str": "result = str(Key('k'))",
    "base_repr_override": 'result = (repr(Quiet(1)), BaseException.__repr__(Quiet(1)))',
    "own_new": 'result = (Exception.__new__ is BaseException.__new__, KeyError.__new__ is LookupError.__new__, Exception.__new__(ValueError, 1).args)',
    "new_unsafe": "Exception.__new__(OSError, 2, 'x')",
    "new_owner": 'KeyError.__new__(int)',
    "dict_getset": "e = ValueError()\ne.x = 1\nd = vars(BaseException)['__dict__']\nresult = (repr(d), d.__get__(e))",
    "own_init": "e = SystemExit(5)\nSystemExit.__init__(e, 7)\nresult = ('__init__' in vars(SystemExit), '__init__' in vars(ValueError), e.code)",
    "base_init_args_only": "e = SystemExit(5)\nBaseException.__init__(e, 7)\nresult = (e.code, e.args)",
    "new_args_only": "e = SystemExit.__new__(SystemExit, 5)\nresult = (e.code, e.args)",
    "init_receiver": "SystemExit.__init__(ValueError())",
    "oserror_use_init": "class Q(OSError):\n    def __init__(self, *a): pass\nresult = (Q(2, 'x').args, Q(2, 'x').errno, OSError.__new__(OSError, 2, 'x').errno)",
    "group_module": "result = (vars(ExceptionGroup)['__module__'], ExceptionGroup('m', [ValueError()]).__weakref__)"
}


TYPES = {name: value for name, value in list(globals().items()) if isinstance(value, type) and name[0].isupper()}


def generated(p):
    return shown(p["op"], p["cls"], p["args"])


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
