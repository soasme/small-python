# spec: PLS-315 18.1
# description: Raising, chaining (__cause__, __context__, __suppress_context__), tracebacks, groups.
from harness import *

try:
    try:
        raise KeyError("a")
    except KeyError:
        raise ValueError("b")
except ValueError as e:
    assert_type(e.__context__, KeyError)
    assert_is(e.__cause__, None)
    assert_false(e.__suppress_context__)

try:
    raise ValueError("x") from KeyError("y")
except ValueError as e:
    assert_type(e.__cause__, KeyError)
    assert_true(e.__suppress_context__)
try:
    try:
        raise KeyError
    except KeyError:
        raise ValueError from None
except ValueError as e:
    assert_is(e.__cause__, None)
    assert_true(e.__suppress_context__)
    assert_type(e.__context__, KeyError)

assert_raises(TypeError, run, "raise 1")
assert_raises(TypeError, run, "raise ValueError from 1")
e = assert_raises(ValueError, run, "raise ValueError")
assert_eq(e.args, ())
class Cls(Exception):
    def __init__(self): super().__init__("built")
e = assert_raises(Cls, run, "raise Cls from KeyError", {"Cls": Cls})
assert_type(e.__cause__, KeyError)
assert_raises(RuntimeError, run, "raise")
# Bare raise re-raises the handled exception, even from a nested function.
def reraise(): raise
try:
    try:
        raise OSError(2, "nope")
    except OSError:
        reraise()
except OSError as e:
    assert_eq(e.errno, 2)

# Tracebacks and with_traceback.
def thrower(): raise IndexError
try:
    thrower()
except IndexError as e:
    tb = e.__traceback__
    assert_eq(tb.tb_frame.f_code.co_name, "<module>")
    assert_eq(tb.tb_next.tb_frame.f_code.co_name, "thrower")
    e2 = Exception().with_traceback(tb)
    assert_is(e2.__traceback__, tb)

# finally always runs; return in finally overrides.
def fin():
    try:
        return 1
    finally:
        log.append("fin")
log = []
assert_eq(fin(), 1)
assert_eq(log, ["fin"])
def override():
    try:
        raise ValueError
    finally:
        return "swallowed"
assert_eq(override(), "swallowed")

# The handled exception is visible as the context of new exceptions.
def context_in_finally():
    try:
        raise KeyError
    finally:
        pass
assert_raises(KeyError, context_in_finally)

# Exception hierarchy facts.
assert_true(issubclass(KeyboardInterrupt, BaseException))
assert_false(issubclass(KeyboardInterrupt, Exception))
assert_true(issubclass(ZeroDivisionError, ArithmeticError))
assert_true(issubclass(ModuleNotFoundError, ImportError))
assert_true(issubclass(FileNotFoundError, OSError))
assert_is(EnvironmentError, OSError)
assert_is(IOError, OSError)
assert_true(issubclass(RecursionError, RuntimeError))
assert_true(issubclass(PythonFinalizationError, RuntimeError))
assert_true(issubclass(IndentationError, SyntaxError))
assert_true(issubclass(TabError, IndentationError))
assert_true(issubclass(UnicodeDecodeError, ValueError))
assert_true(issubclass(ExceptionGroup, Exception))
assert_true(issubclass(BaseExceptionGroup, BaseException))
assert_eq(type(OSError(2, "x")), FileNotFoundError)
assert_eq(str(KeyError("k")), "'k'")
assert_eq(repr(ValueError(1, 2)), "ValueError(1, 2)")
assert_eq(StopIteration(5).value, 5)
assert_eq(SystemExit(3).code, 3)
e = ValueError()
e.add_note("note")
assert_eq(e.__notes__, ["note"])
assert_raises(TypeError, e.add_note, 1)
assert_eq(AttributeError("m", name="n", obj=1).name, "n")
assert_eq(NameError("m", name="q").name, "q")
assert_eq(ImportError("m", name="a", path="p").path, "p")

# Recursion limit is a RecursionError.
def deep(): return deep()
assert_raises(RecursionError, deep)

# add_note requires a str.
e = assert_raises(TypeError, ValueError().add_note, 1)
assert_eq(str(e), "add_note() argument must be str, not int")
# An operation reports the line where its expression begins, after its
# operands have been evaluated on later lines.
def failing_line(function):
    try:
        function()
    except Exception as error:
        tb = error.__traceback__
        while tb.tb_next: tb = tb.tb_next
        return tb.tb_lineno - function.__code__.co_firstlineno
def spans_lines():
    return (1 +
        "s")
def attribute_line():
    return (None
        .missing)
def subscript_line():
    return [1,
        2][5]
assert_eq([failing_line(f) for f in (spans_lines, attribute_line, subscript_line)], [1, 2, 1])
