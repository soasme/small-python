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
    "delattr_hook_calls": "log = []\nclass H:\n    def __delattr__(self, n):\n        log.append(n)\n        if n == 'bad': raise LookupError(n)\n"
                          "class P:\n    p = property(lambda s: 1, None, lambda s: log.append('deleter'))\n"
                          "class D:\n    def __get__(self, i, o): return 1\n    def __set__(self, i, v): pass\n"
                          "    def __delete__(self, i): log.append('delete')\nclass Q:\n    d = D()\n"
                          "def bad():\n    try: delattr(H(), 'bad')\n    except LookupError as e: return type(e).__name__\n"
                          "result = (delattr(H(), 'x'), delattr(P(), 'p'), delattr(Q(), 'd'), bad(), log)",
    "staticmethod_instance_call": ("log = []\nclass F:\n    def __call__(s, *a):\n        log.append(a)\n        return sum(a)\n"
                                   "result = (staticmethod(F())(1, 2), log)"),
    "wrapper_name_copy": ("log = []\nclass F:\n    def __getattr__(s, n):\n        log.append(n)\n        return 'n_' + n\n"
                          "w = staticmethod(F())\nresult = (w.__name__, log)"),
    "wrapper_computed_reads": "log = []\nclass Flag:\n    def __init__(self, v): self.v = v\n    def __bool__(self):\n        for _ in (): pass\n        log.append(self.v); return self.v\nclass Odd:\n    def __getattr__(self, name):\n        for _ in (): pass\n        log.append(name)\n        return Flag(True) if name == '__isabstractmethod__' else 'odd'\n    def __call__(self, *a): return 1\ndef f(self): pass\nf.__isabstractmethod__ = Flag(False)\nresult = (getattr(property(f, Odd()), '__isabstractmethod__'), hasattr(property(Odd()), '__name__'), property(Odd()).__name__.upper(), log)",
    "property_abstract_truth": ("log = []\nclass B:\n    def __init__(s, v): s.v = v\n    def __bool__(s):\n        log.append(s.v)\n        return bool(s.v)\n"
                                "def a(s): pass\ndef b(s, v): pass\ndef d(s): pass\n"
                                "a.__isabstractmethod__ = B(0)\nb.__isabstractmethod__ = B(1)\nd.__isabstractmethod__ = B(2)\n"
                                "result = (property(a, b, d).__isabstractmethod__, log)"),
    "property_subclass_doc": ("log = []\nclass G:\n    @property\n    def __doc__(self):\n        log.append('doc')\n        return 'd'\n"
                              "class R(property): pass\nresult = (R(G()).__doc__, log)"),
    "property_copy_calls": ("log = []\nclass Q(property):\n    def __init__(self, *a):\n        log.append(len(a))\n        super().__init__(*a)\n"
                            "p = Q(lambda s: 1)\nq = p.setter(lambda s, v: None)\nresult = (type(q).__name__, log, q.fget is p.fget)"),
    "property_get_calls": "log = []\nclass Q(property):\n    def __get__(self, obj, owner=None):\n        log.append('own')\n        return ('q', super().__get__(obj, owner))\n"
                          "class K:\n    @Q\n    def q(self):\n        for _ in (): pass\n        log.append('get')\n        return 2\n"
                          "k = K()\nd = K.__dict__['q']\n"
                          "result = (k.q, property.__get__(d, k), super(Q, d).__get__(k, K), d.__get__(None, K) is d, log)",
    "slots_setattr": 'p = P()\np.t = 1',
    "slots_vars": 'result = vars(P())',
    "vars_no_arg": 'def f():\n    a = 1\n    return vars()\nresult = f()',
    "vars_module": 'result = type(vars(type(P))).__name__',
    "dir_module_property": "n = []\nclass M(type(__import__('builtins'))):\n"
                           "    @property\n    def __dict__(self):\n        for _ in (): pass\n        n.append(1)\n"
                           "        return {'b': 1, 'a': 2}\nresult = (dir(M('m')), len(n))",
    "dir_sorted": "class D:\n    b = 1\n    a = 2\nresult = [n for n in dir(D) if not n.startswith('_')]",
    "dir_hook_calls": "n = []\nclass D:\n    def __dir__(self):\n        for _ in (): pass\n        n.append(1)\n        return ('z', 'a', 'y')\nresult = (dir(D()), len(n))",
    "dir_locals_keys": "n = []\nclass NS:\n    def __getitem__(s, k): raise KeyError(k)\n    def keys(s):\n        for _ in (): pass\n        n.append('keys')\n        return iter(['q', 'p'])\nresult = (eval('dir()', {}, NS()), n)",
    "dir_hook": "class D:\n    def __dir__(self): return ['z', 'a']\nresult = dir(D())",
    "dir_hook_generator": "class D:\n    def __dir__(self):\n        for _ in range(2): pass\n        yield 'b'; yield 'a'\nresult = dir(D())",
    "dir_hook_iterable": "class I:\n    def __iter__(self):\n        for _ in range(2): pass\n        return iter(['y', 'x'])\n"
                         "class D:\n    def __dir__(self): return I()\nresult = dir(D())",
    "dir_hook_raises": "class D:\n    def __dir__(self):\n        yield 'a'; raise KeyError('e')\nresult = dir(D())",
    "dir_hook_bad": 'class D:\n    def __dir__(self): return 1\nresult = dir(D())',
    "callable_unread": 'def fail(self): raise AttributeError("x")\nclass F:\n    __call__ = property(fail)\n'
                       'class N:\n    __call__ = None\nclass I(int): pass\nresult = (callable(F()), callable(N()), callable(I()))',
    "callable_forms": 'class K:\n    def __call__(self): pass\nresult = (callable(K), callable(K()), callable(P()), callable(len), callable(1))',
    "id_identity": 'a = []\nresult = (id(a) == id(a), id([]) == id([]) or True, type(id(a)).__name__)',
    "hash_big": 'result = hash(H()) == hash(2 ** 70)',
    "hash_bad": 'result = hash(HN())',
    "hash_eq_only": 'result = hash(Eq())',
    "hash_method_object": "log = []\nclass Hasher:\n    def hash(self, *args):\n        for _ in (): pass\n        log.append(len(args)); return 7\n"
                          "class HM:\n    __hash__ = Hasher().hash\nk = HM()\nresult = (hash(k), {k: 1}[k], k in {k}, log)",
    "hash_tuple": "class T:\n    def __init__(s, v): s.v = v\n    def __hash__(s):\n        for _ in range(2): pass\n        log.append(s.v)\n        return s.v\n"
                  "log = []\nt = (T(1), (T(2), 3))\nresult = (hash(t) == hash((1, (2, 3))), hash(t) == hash((1, (2, 3))), log)",
    "hash_tuple_fails": "class R:\n    def __hash__(s):\n        for _ in range(2): pass\n        log.append(0)\n        raise ValueError('r')\n"
                        "log = []\nbad = (1, R())\nfor _ in range(2):\n    try: hash(bad)\n    except ValueError: pass\nresult = log",
    "hash_numeric": 'result = (hash(1) == hash(1.0) == hash(True), hash(-1), hash(-2))',
    "type_one_arg": 'result = (type(1), type(type), type(P()).__name__)',
    "type_three_args": "T = type('T', (P,), {'k': 1, '__module__': 'm'})\nresult = (T.__name__, T.__bases__, T.k, T.__module__)",
    "type_two_args": "result = type('T', ())",
    "type_bad_bases": "result = type('T', 1, {})",
    "type_bad_dict": "result = type('T', (), [])",
    "builtin_missing_before_clash": "result = pow(2, base=2)",
    "typevartuple_total": "def f[*Ts](): pass\nresult = type(f.__type_params__[0])('a', 'b', x=1, y=2, z=3, u=4, v=5)",
    "typevartuple_suggest": "def f[*Ts](): pass\nresult = type(f.__type_params__[0])('a', dfault=1)",
    "paramspecargs_missing": "def f[**P](): pass\nresult = type(f.__type_params__[0].args)()",
    "ga_iterator_create": "result = type(iter(list[int]))(list[int])",
    "type_bad_dict_local": "def make():\n    class Local: pass\n    return Local()\nresult = type('T', (), make())",
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
