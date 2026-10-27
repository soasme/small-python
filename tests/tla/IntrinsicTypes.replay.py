# Replays IntrinsicTypes.tla: each case runs the spec's source in a fresh
# namespace and compares the repr of its result (or the exception and its
# message, a SyntaxError's without the location) with the model's.
FIELDS = ("program", "outcome")
CASES = ""  # filled in by tests/tla_check.py, with walks() and states()
import sys
import types


def _f(): pass
def _g(): yield
async def _c(): pass
async def _ag(): yield
class _S:
    __slots__ = ("a",)
    def m(self): pass
def _cell():
    v = 1
    return (lambda: v).__closure__[0]
try:
    raise ValueError
except ValueError as _e:
    _tb = _e.__traceback__

SAMPLES = {
    "FunctionType": lambda: _f, "LambdaType": lambda: (lambda: 0), "GeneratorType": lambda: _g(),
    "CoroutineType": lambda: _c(), "AsyncGeneratorType": lambda: _ag(), "CodeType": lambda: _f.__code__,
    "CellType": _cell, "MethodType": lambda: _S().m, "BuiltinFunctionType": lambda: len,
    "BuiltinMethodType": lambda: [].append, "WrapperDescriptorType": lambda: object.__init__,
    "MethodWrapperType": lambda: object().__str__, "NotImplementedType": lambda: NotImplemented,
    "MethodDescriptorType": lambda: str.join, "ClassMethodDescriptorType": lambda: dict.__dict__["fromkeys"],
    "ModuleType": lambda: sys, "TracebackType": lambda: _tb, "FrameType": lambda: sys._getframe(),
    "GetSetDescriptorType": lambda: int.__dict__["real"], "MemberDescriptorType": lambda: _S.a,
    "MappingProxyType": lambda: type.__dict__ if False else _S.__dict__, "EllipsisType": lambda: ...,
    "NoneType": lambda: None, "GenericAlias": lambda: list[int], "UnionType": lambda: int | str,
    "FrameLocalsProxyType": lambda: sys._getframe().f_locals,
}


def intrinsic(name):
    sample = SAMPLES[name]()
    kind = type(sample)
    result = (kind.__name__, getattr(types, name) is kind, kind.__module__, isinstance(sample, getattr(types, name)))
    if name in ("CoroutineType",): sample.close()
    return repr(result)

SOURCES = {
    "method_ctor": 'import types\nclass A: pass\ndef f(self, x): return (self, x)\na = A()\nm = types.MethodType(f, a)\nresult = (m.__self__ is a, m.__func__ is f, m(1)[1])',
    "method_not_callable": 'import types\ntypes.MethodType(1, 2)',
    "module_ctor": "import types\nm = types.ModuleType('m', 'doc')\nm.x = 1\nresult = (m.__name__, m.__doc__, m.x, repr(m))",
    "module_bad_name": 'import types\ntypes.ModuleType(1)',
    "cell_empty": 'import types\ntypes.CellType().cell_contents',
    "cell_set": 'import types\nc = types.CellType(1)\nc.cell_contents = 2\nresult = c.cell_contents',
    "cell_shared": 'def f():\n    v = 1\n    def g(): return v\n    g.__closure__[0].cell_contents = 5\n    return v\nresult = f()',
    "proxy_readonly": "import types\np = types.MappingProxyType({'a': 1})\np['a'] = 2",
    "proxy_live": "import types\nd = {'a': 1}\np = types.MappingProxyType(d)\nd['b'] = 2\nresult = (len(p), p['b'], 'b' in p, p.get('c', 0))",
    "proxy_bad": 'import types\ntypes.MappingProxyType([1])',
    "proxy_or": "import types\nresult = types.MappingProxyType({'a': 1}) | {'b': 2}",
    "proxy_copy": "import types\nc = types.MappingProxyType({'a': 1}).copy()\nresult = (type(c).__name__, c)",
    "class_dict_proxy": "class A:\n    x = 1\nA.__dict__['x'] = 2",
    "function_ctor": "import types\ndef f(): return x\ng = types.FunctionType(f.__code__, {'x': 5}, 'g')\nresult = (g(), g.__name__)",
    "code_replace": "def f(): pass\nresult = f.__code__.replace(co_name='g').co_name",
    "notimplemented_ctor": 'result = type(NotImplemented)() is NotImplemented',
    "none_ctor": 'result = type(None)() is None',
    "classmethod_descr_repr": "result = repr(dict.__dict__['fromkeys'])",
    "classmethod_descr_call": "result = dict.__dict__['fromkeys'](dict, 'ab')",
    "classmethod_descr_get": "result = dict.__dict__['fromkeys'].__get__(None, dict)('a')",
    "classmethod_descr_instance": "result = dict.__dict__['fromkeys'].__get__({})('x')",
    "classmethod_descr_objclass": "d = dict.__dict__['fromkeys']\nresult = (d.__objclass__ is dict, d.__name__, d.__qualname__, callable(d))",
    "classmethod_descr_no_arg": "dict.__dict__['fromkeys']()",
    "classmethod_descr_not_type": "dict.__dict__['fromkeys'](1, 'a')",
    "classmethod_descr_not_subtype": "dict.__dict__['fromkeys'](int, 'a')",
    "getset_get": "result = int.__dict__['real'].__get__(3)",
    "getset_readonly": "int.__dict__['real'].__set__(3, 4)",
    "member_unset": "class S:\n    __slots__ = ('a',)\nS.a.__get__(S())",
    "member_set": "class S:\n    __slots__ = ('a',)\ns = S()\nS.a.__set__(s, 7)\nresult = (s.a, S.a.__name__, S.a.__objclass__ is S)",
    "method_descr_wrong_type": 'str.join(1, [])',
    "method_descr_objclass": 'result = (str.join.__objclass__ is str, str.join.__name__, str.join.__qualname__)',
    "wrapper_descr_call": "result = (str.__dict__['__add__']('a', 'b'), object.__init__.__objclass__ is object)",
    "method_wrapper_self": 'o = object()\nresult = (o.__str__.__self__ is o, o.__str__.__name__)',
    "builtin_self": 'l = []\nresult = (len.__self__.__name__, l.append.__self__ is l)',
    "generator_no_ctor": 'import types\ntypes.GeneratorType()',
    "function_no_subclass": 'import types\nclass F(types.FunctionType): pass',
    "traceback_fields": 'def f(): 1 / 0\ntry:\n    f()\nexcept ZeroDivisionError as e:\n    tb = e.__traceback__\nresult = (tb.tb_frame.f_code.co_name, tb.tb_next.tb_frame.f_code.co_name, tb.tb_next.tb_next)',
    "frame_back": 'import sys\ndef f(): return sys._getframe().f_back.f_code.co_name\ndef g(): return f()\nresult = g()'
}




def generated(p):
    return intrinsic(p["name"])


def run(p):
    if "case" not in p:
        return generated(p)
    namespace = {}
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
