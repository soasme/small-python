# spec: PLS-315 21.4
# description: Programs on except*, each with the output CPython 3.15 gives.
from harness import *

check_program('''def run(f):
    try: f()
    except BaseException as e: print(type(e).__name__, repr(e), getattr(e, "exceptions", None))
def a():
    try: raise TypeError(1)
    except* ValueError: pass
def b():
    try: raise ValueError(1)
    except* ValueError: raise
def c():
    try: raise ValueError(1)
    except* ValueError as e: print("caught", repr(e)); raise KeyError(2)
def d():
    try: raise ExceptionGroup("g", [ValueError(1), TypeError(2), ExceptionGroup("n", [ValueError(3), KeyError(4)])])
    except* ValueError as e: print("v", repr(e))
    except* KeyError as e: print("k", repr(e)); raise
def e():
    try: raise ExceptionGroup("g", [ValueError(1), TypeError(2)])
    except* ValueError: raise RuntimeError("new")
    except* TypeError: pass
for f in [a, b, c, d, e]: run(f)
eg = ExceptionGroup("m", [ValueError(1), TypeError(2)])
print(str(eg), eg.message, eg.exceptions, eg.args, repr(eg.split(ValueError)), repr(eg.subgroup(lambda x: isinstance(x, TypeError))))
print(type(BaseExceptionGroup("x", [ValueError()])).__name__, type(BaseExceptionGroup("x", [KeyboardInterrupt()])).__name__)
for bad in [lambda: ExceptionGroup("x", []), lambda: ExceptionGroup(1, [ValueError()]), lambda: ExceptionGroup("x", [1]), lambda: ExceptionGroup("x", [KeyboardInterrupt()]), lambda: ExceptionGroup("x"), lambda: ExceptionGroup("x", 5)]:
    try: bad()
    except TypeError as err: print("TypeError", err)
    except ValueError as err: print("ValueError", err)
''',
              '''TypeError TypeError(1) None
ExceptionGroup ExceptionGroup('', (ValueError(1),)) (ValueError(1),)
caught ExceptionGroup('', (ValueError(1),))
KeyError KeyError(2) None
v ExceptionGroup('g', [ValueError(1), ExceptionGroup('n', [ValueError(3)])])
k ExceptionGroup('g', [ExceptionGroup('n', [KeyError(4)])])
ExceptionGroup ExceptionGroup('g', [TypeError(2), ExceptionGroup('n', [KeyError(4)])]) (TypeError(2), ExceptionGroup('n', [KeyError(4)]))
RuntimeError RuntimeError('new') None
m (2 sub-exceptions) m (ValueError(1), TypeError(2)) ('m', [ValueError(1), TypeError(2)]) (ExceptionGroup('m', [ValueError(1)]), ExceptionGroup('m', [TypeError(2)])) ExceptionGroup('m', [TypeError(2)])
ExceptionGroup BaseExceptionGroup
ValueError second argument (exceptions) must be a non-empty sequence
TypeError BaseExceptionGroup.__new__() argument 1 must be str, not int
ValueError Item 0 of second argument (exceptions) is not an exception
TypeError Cannot nest BaseExceptions in an ExceptionGroup
TypeError BaseExceptionGroup.__new__() takes exactly 2 arguments (1 given)
TypeError second argument (exceptions) must be a sequence
''')

check_program('for code in ["try: pass\\nexcept* ValueError: pass\\nexcept TypeError: pass", "try: pass\\nexcept*: pass",\n             "def f():\\n    try: pass\\n    except* ValueError: return 1", "for i in []:\\n    try: pass\\n    except* ValueError: break",\n             "for i in []:\\n    try: pass\\n    except* ValueError:\\n        for j in []: break", "try: pass\\nexcept* ValueError:\\n    def g(): return 1",\n             "try: pass\\nexcept ValueError, TypeError as e: pass", "try: pass\\nexcept ValueError, TypeError: pass",\n             "while True:\\n    try: pass\\n    except* ValueError: continue"]:\n    try: compile(code, "<s>", "exec"); print("ok")\n    except SyntaxError as e: print("SyntaxError", e.msg)\ntry:\n    1 / 0\nexcept ValueError, ZeroDivisionError:\n    print("pep758")\ndef flow(exc):\n    log = []\n    try:\n        try:\n            if exc: raise exc\n        except* ValueError as e:\n            log.append(("v", repr(e)))\n        except* (TypeError, KeyError) as e:\n            log.append(("tk", repr(e)))\n        else:\n            log.append("else")\n        finally:\n            log.append("finally")\n    except BaseException as outer:\n        log.append(("outer", repr(outer)))\n    return log\nfor exc in [None, ValueError(1), ExceptionGroup("g", [TypeError(1), KeyError(2), OSError(3)]), OSError(9)]:\n    print(flow(exc))\ntry:\n    try: raise ExceptionGroup("g", [ValueError(1)])\n    except* ExceptionGroup: pass\nexcept TypeError as e: print("TypeError", e)\ntry:\n    try: raise ValueError\n    except* 5: pass\nexcept TypeError as e: print("TypeError", e)\nclass MyEG(ExceptionGroup):\n    def derive(self, excs): return MyEG(self.message + "!", excs)\ne = MyEG("m", [ValueError(1), TypeError(2)])\ne.add_note("note")\nm, r = e.split(ValueError)\nprint(type(m).__name__, m.message, m.__notes__, r.__notes__, m.__notes__ is e.__notes__)\nprint(e.subgroup((TypeError, KeyError)), e.subgroup(lambda x: False), e.split(BaseException))\ntry: e.split(5)\nexcept TypeError as err: print(err)\ntry:\n    try: raise MyEG("x", [ValueError(1), TypeError(2)])\n    except* ValueError: pass\nexcept ExceptionGroup as g: print(type(g).__name__, repr(g))\neg = BaseExceptionGroup("b", [KeyboardInterrupt(), ValueError()])\nprint(repr(eg), isinstance(eg, Exception), isinstance(ExceptionGroup("x", [ValueError()]), Exception))\nprint(issubclass(ExceptionGroup, BaseExceptionGroup), ExceptionGroup.__mro__)\nprint(str(ExceptionGroup("one", [ValueError()])), ExceptionGroup("x", (ValueError(),)).args)\ndef nested():\n    try:\n        try: raise ExceptionGroup("a", [ValueError(1), TypeError(2)])\n        except* ValueError: raise KeyError("k")\n    except* KeyError as e: print("caught", repr(e))\n    except* TypeError as e: print("rest", repr(e))\nnested()\ntry:\n    try: raise ExceptionGroup("g", [ValueError(1)])\n    except* ValueError as e: raise e\nexcept ExceptionGroup as g: print("raise e", repr(g))\nprint(issubclass(FileNotFoundError, OSError), IOError is OSError, issubclass(UserWarning, Warning), TimeoutError.__mro__[1].__name__)\n',
              '''SyntaxError cannot have both 'except' and 'except*' on the same 'try'
SyntaxError expected one or more exception types
SyntaxError 'break', 'continue' and 'return' cannot appear in an except* block
SyntaxError 'break', 'continue' and 'return' cannot appear in an except* block
ok
ok
SyntaxError multiple exception types must be parenthesized when using 'as'
ok
SyntaxError 'break', 'continue' and 'return' cannot appear in an except* block
pep758
['else', 'finally']
[('v', "ExceptionGroup('', (ValueError(1),))"), 'finally']
[('tk', "ExceptionGroup('g', [TypeError(1), KeyError(2)])"), 'finally', ('outer', "ExceptionGroup('g', [OSError(3)])")]
['finally', ('outer', 'OSError(9)')]
TypeError catching ExceptionGroup with except* is not allowed. Use except instead.
TypeError catching classes that do not inherit from BaseException is not allowed
MyEG m! ['note'] ['note'] False
m! (1 sub-exception) None (MyEG('m', [ValueError(1), TypeError(2)]), None)
expected an exception type, a tuple of exception types, or a callable (other than a class)
MyEG MyEG('x!', [TypeError(2)])
BaseExceptionGroup('b', [KeyboardInterrupt(), ValueError()]) False True
True (<class 'ExceptionGroup'>, <class 'BaseExceptionGroup'>, <class 'Exception'>, <class 'BaseException'>, <class 'object'>)
one (1 sub-exception) ('x', (ValueError(),))
caught ExceptionGroup('', [KeyError('k')])
rest ExceptionGroup('', [ExceptionGroup('a', [TypeError(2)])])
raise e ExceptionGroup('g', [ValueError(1)])
True True True OSError
''')
