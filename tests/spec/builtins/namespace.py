# spec: PLS-315 19, 19.1, 19.2, 19.4, 18.4, 21.2
# description: The built-in namespace has exactly the Core names, plus only the host-provided names of 19.4.
from harness import *

builtins = host.module_cache()["builtins"]
CORE = set("""None False True NotImplemented Ellipsis __debug__ __name__ __doc__ __package__ __loader__ __spec__
object type super property staticmethod classmethod sentinel bool int float complex str bytes bytearray memoryview
list tuple range slice dict frozendict set frozenset enumerate filter map reversed zip
abs aiter all anext any ascii bin oct hex breakpoint callable chr compile delattr getattr hasattr setattr dir divmod
eval exec format globals hash id input isinstance issubclass iter len locals max min next open ord pow print repr
round sorted sum vars __import__ __build_class__ __lazy_import__
BaseException SystemExit KeyboardInterrupt GeneratorExit BaseExceptionGroup Exception ExceptionGroup ArithmeticError
FloatingPointError OverflowError ZeroDivisionError AssertionError AttributeError BufferError EOFError MemoryError
ReferenceError StopIteration StopAsyncIteration SystemError TypeError ImportError ModuleNotFoundError ImportCycleError
LookupError IndexError KeyError NameError UnboundLocalError OSError EnvironmentError IOError BlockingIOError
ChildProcessError FileExistsError FileNotFoundError InterruptedError IsADirectoryError NotADirectoryError
PermissionError ProcessLookupError TimeoutError ConnectionError BrokenPipeError ConnectionAbortedError
ConnectionRefusedError ConnectionResetError RuntimeError NotImplementedError PythonFinalizationError RecursionError
SyntaxError IndentationError TabError ValueError UnicodeError UnicodeDecodeError UnicodeEncodeError
UnicodeTranslateError Warning BytesWarning DeprecationWarning EncodingWarning FutureWarning ImportWarning
PendingDeprecationWarning ResourceWarning RuntimeWarning SyntaxWarning UnicodeWarning UserWarning""".split())
HOST = {"exit", "quit", "help", "copyright", "credits", "license", "_IncompleteInputError", "_"}
names = set(dir(builtins))
assert_eq(sorted(CORE - names), [])
assert_eq(sorted(names - CORE - HOST), [])

# 19.1 value properties.
assert_is(builtins.__dict__["None"], None)
assert_is(builtins.__dict__["True"], True)
assert_is(builtins.Ellipsis, ...)
assert_is(builtins.NotImplemented, NotImplemented)
assert_eq(builtins.__name__, "builtins")
assert_is(__debug__, True)
assert_eq(assert_syntax_error("__debug__ = 1\n").msg, "cannot assign to __debug__")
assert_syntax_error("def f(__debug__): pass\n")
# 19.2: the constructors and the exception classes are classes in builtins.
for name in ("object", "type", "int", "frozendict", "sentinel", "zip", "ExceptionGroup", "ImportCycleError"):
    cls = getattr(builtins, name)
    assert_type(cls, type)
    assert_eq(cls.__module__, "builtins")
    assert_eq(cls.__name__, name)
assert_is(builtins.EnvironmentError, OSError)
assert_is(builtins.IOError, OSError)
assert_eq(ExceptionGroup.__mro__, (ExceptionGroup, BaseExceptionGroup, Exception, BaseException, object))
# The T.__new__(S) checks.
e = assert_raises(TypeError, int.__new__, 1)
assert_eq(str(e), "int.__new__(X): X is not a type object (int)")
e = assert_raises(TypeError, int.__new__, str)
assert_eq(str(e), "int.__new__(str): str is not a subtype of int")
e = assert_raises(TypeError, int.__new__, bool)
assert_eq(str(e), "int.__new__(bool) is not safe, use bool.__new__()")
# 19.4: exit and quit, when present, raise SystemExit.
for name in ("exit", "quit"):
    if name in names:
        assert_raises(SystemExit, getattr(builtins, name))
# A program may change the namespace; LoadGlobal sees it.
builtins.spec_added = 42
try:
    assert_eq(spec_added, 42)
finally:
    del builtins.spec_added
assert_raises(NameError, lambda: spec_added)
