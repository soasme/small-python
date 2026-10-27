# Replays BuiltinsObjects.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
class A:
    x = 1
class B(A):
    def __init__(self): self.y = 2
class C:
    def __getattr__(self, name):
        if name.startswith("m"): return "dyn:" + name
        raise AttributeError(name)


OBJECTS = {"a": A, "b": B, "c": C, "one": lambda: 1}
INFOS = {"A": A, "B": B, "AC": (A, C), "BorC": B | C, "int": int, "object": object, "empty": (), "bool": bool, "nested": ((B,), (int,))}
NAMES = ["x", "y", "m", "real"]


def objects(op, obj, arg):
    o = OBJECTS[obj]()
    try:
        if op == "isinstance": return repr(isinstance(o, INFOS[arg]))
        if op == "issubclass": return repr(issubclass(type(o), INFOS[arg]))
        if op == "getattr": return repr(getattr(o, arg, "d"))
        if op == "hasattr": return repr(hasattr(o, arg))
        if op == "delattr":
            delattr(o, arg)
            return repr(hasattr(o, arg))
        if op == "setattr":
            setattr(o, arg, 5)
            return repr((getattr(o, arg), arg in vars(o)))
    except (AttributeError, TypeError) as error:
        return "%s: %s" % (type(error).__name__, error)
class P:
    __slots__ = ("s",)
class H:
    def __hash__(self): return 2 ** 70
class HN:
    def __hash__(self): return "x"
class Eq:
    def __eq__(self, other): return True
class Meta(type):
    def __instancecheck__(cls, obj): return obj == "yes"
    def __subclasscheck__(cls, sub): return sub is int
class Q(metaclass=Meta): pass

SOURCES = {
    "getattr_nonstr": 'result = getattr(1, 2)',
    "getattr_missing": "result = getattr(1, 'nope')",
    "setattr_nonstr": 'result = setattr(P(), 1, 2)',
    "hasattr_propagates": "class E:\n    @property\n    def p(self): raise ValueError('inner')\nresult = hasattr(E(), 'p')",
    "hasattr_attributeerror": "class E:\n    @property\n    def p(self): raise AttributeError('x')\nresult = hasattr(E(), 'p')",
    "slots_setattr": 'p = P()\np.t = 1',
    "slots_vars": 'result = vars(P())',
    "vars_no_arg": 'def f():\n    a = 1\n    return vars()\nresult = f()',
    "vars_module": 'result = type(vars(type(P))).__name__',
    "dir_sorted": "class D:\n    b = 1\n    a = 2\nresult = [n for n in dir(D) if not n.startswith('_')]",
    "dir_hook": "class D:\n    def __dir__(self): return ['z', 'a']\nresult = dir(D())",
    "dir_hook_bad": 'class D:\n    def __dir__(self): return 1\nresult = dir(D())',
    "callable_forms": 'class K:\n    def __call__(self): pass\nresult = (callable(K), callable(K()), callable(P()), callable(len), callable(1))',
    "id_identity": 'a = []\nresult = (id(a) == id(a), id([]) == id([]) or True, type(id(a)).__name__)',
    "hash_big": 'result = hash(H()) == hash(2 ** 70)',
    "hash_bad": 'result = hash(HN())',
    "hash_eq_only": 'result = hash(Eq())',
    "hash_numeric": 'result = (hash(1) == hash(1.0) == hash(True), hash(-1), hash(-2))',
    "type_one_arg": 'result = (type(1), type(type), type(P()).__name__)',
    "type_three_args": "T = type('T', (P,), {'k': 1, '__module__': 'm'})\nresult = (T.__name__, T.__bases__, T.k, T.__module__)",
    "type_two_args": "result = type('T', ())",
    "type_bad_bases": "result = type('T', 1, {})",
    "type_bad_dict": "result = type('T', (), [])",
    "type_bad_name": 'result = type(1, (), {})',
    "type_qualname_kw": "T = type('T', (), {'__qualname__': 'Q.T'})\nresult = T.__qualname__",
    "isinstance_hook": "result = (isinstance('yes', Q), isinstance('no', Q), issubclass(int, Q), issubclass(str, Q))",
    "isinstance_bad": 'result = isinstance(1, 1)',
    "issubclass_bad_first": 'result = issubclass(1, int)',
    "issubclass_bad_second": 'result = issubclass(int, [int])',
    "object_no_attrs": 'o = object()\no.x = 1',
    "object_args": 'result = object(1)',
    "object_dir_has": "result = ('__dict__' in dir(object()), '__init__' in dir(object()))",
    "delattr_class": "class W:\n    k = 1\ndelattr(W, 'k')\nresult = hasattr(W, 'k')",
    "setattr_builtin_type": "setattr(int, 'k', 1)",
    "getattr_type_default": "result = getattr(int, 'nope', None)",
    "super_zero_arg": "class S0:\n    def f(self): return 'S0'\nclass S1(S0):\n    def f(self): return 'S1>' + super().f()\nresult = S1().f()",
    "globals_identity": 'result = globals() is globals()',
    "memoryview_builtin": "result = memoryview(b'ab')[1]",
    "repr_builtin": 'result = (repr(P).startswith("<class \'"), repr(len), repr(None))'
}


TYPES = {name: value for name, value in list(globals().items()) if isinstance(value, type) and name[0].isupper()}


def generated(p):
    return objects(p["op"], p["obj"], p["arg"])


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
