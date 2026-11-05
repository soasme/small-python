# spec: PLS-315 21.1.2, 21.3.1, 21.3.3, 21.3.4, 21.3.5, 21.3.6, 21.4.1
# description: The exception classes' own __init__ set their attributes; __new__ sets only args, and BaseException.__init__ only args.
from harness import *

# Each class that sets attributes from its arguments owns an __init__.
for cls in (StopIteration, SystemExit, ImportError, AttributeError, NameError, OSError, SyntaxError,
            UnicodeEncodeError, UnicodeDecodeError, UnicodeTranslateError, BaseExceptionGroup):
    assert_true("__init__" in vars(cls), cls.__name__)
    assert_eq(repr(cls.__init__), f"<slot wrapper '__init__' of '{cls.__name__}' objects>")
for cls in (Exception, ValueError, KeyError, ModuleNotFoundError, FileNotFoundError, ExceptionGroup):
    assert_false("__init__" in vars(cls), cls.__name__)

# __new__ stores args alone.
assert_eq(SystemExit.__new__(SystemExit, 5).code, None)
assert_eq(StopIteration.__new__(StopIteration, 5).value, None)
assert_eq(ImportError.__new__(ImportError, "m").msg, None)
made = SyntaxError.__new__(SyntaxError, "m", ("f", 1, 2, "t"))
assert_eq((made.msg, made.lineno, made.args), (None, None, ("m", ("f", 1, 2, "t"))))
made = UnicodeDecodeError.__new__(UnicodeDecodeError, 1)
assert_eq((made.encoding, made.object, made.start, made.end, made.reason, made.args), (None, None, 0, 0, None, (1,)))
made = OSError.__new__(OSError, 2, "x", "f")
assert_eq((type(made), made.errno, made.strerror, made.filename, made.args), (FileNotFoundError, 2, "x", "f", (2, "x")))

# BaseException.__init__ changes args, nothing else.
error = OSError(2, "x", "f")
BaseException.__init__(error, 3, "y", "g")
assert_eq((error.args, error.errno, error.strerror, error.filename), ((3, "y", "g"), 2, "x", "f"))
error = SystemExit(5)
BaseException.__init__(error, 7)
assert_eq((error.code, error.args), (5, (7,)))
error = ImportError("m")
BaseException.__init__(error, "z")
assert_eq((error.msg, error.args), ("m", ("z",)))
assert_raises(TypeError, BaseException.__init__, ImportError("m"), name="n", message="ImportError() takes no keyword arguments")
error = UnicodeDecodeError("utf-8", b"x", 0, 1, "r")
BaseException.__init__(error, 1)
assert_eq((error.encoding, error.args), ("utf-8", (1,)))

# Each class's own __init__ sets its attributes again.
error = SystemExit(5)
assert_is(SystemExit.__init__(error, 7), None)
assert_eq(error.code, 7)
SystemExit.__init__(error, 1, 2)
assert_eq((error.code, error.args), ((1, 2), (1, 2)))
error = StopIteration(5)
StopIteration.__init__(error, 7)
assert_eq(error.value, 7)
error = ImportError("m", path="p")
ImportError.__init__(error, "z", name="n")
assert_eq((error.msg, error.name, error.path, error.args), ("z", "n", None, ("z",)))
error = ModuleNotFoundError("m")
ImportError.__init__(error, "q", name="z")
assert_eq((error.msg, error.name), ("q", "z"))
error = AttributeError("m")
AttributeError.__init__(error, "z", name="n", obj=1)
assert_eq((error.name, error.obj), ("n", 1))
assert_raises(TypeError, NameError.__init__, NameError(), obj=1, message="NameError() got an unexpected keyword argument 'obj'")
error = SyntaxError("m")
SyntaxError.__init__(error, "z", ("f", 1, 2, "t"))
assert_eq((error.msg, error.lineno, error.text), ("z", 1, "t"))
error = IndentationError("m")
SyntaxError.__init__(error, "q")
assert_eq(error.msg, "q")
error = UnicodeDecodeError("utf-8", b"x", 0, 1, "r")
UnicodeDecodeError.__init__(error, "ascii", b"yy", 1, 2, "q")
assert_eq((error.encoding, error.object, error.start, error.reason), ("ascii", b"yy", 1, "q"))
assert_raises(TypeError, UnicodeDecodeError.__init__, error, 1, message="function takes exactly 5 arguments (1 given)")
group = ExceptionGroup("m", [ValueError()])
BaseExceptionGroup.__init__(group, "z", [KeyError()])
assert_eq((group.message, group.args[0]), ("m", "z"))

# The receiver and keyword checks name the class.
assert_raises(TypeError, StopIteration.__init__, message="descriptor '__init__' of 'StopIteration' object needs an argument")
assert_raises(TypeError, OSError.__init__, ValueError(),
              message="descriptor '__init__' requires a 'OSError' object but received a 'ValueError'")
assert_raises(TypeError, UnicodeDecodeError.__init__, UnicodeEncodeError("ascii", "ab", 0, 1, "r"), "a", b"x", 0, 1, "r",
              message="descriptor '__init__' requires a 'UnicodeDecodeError' object but received a 'UnicodeEncodeError'")
for call, text in ((lambda: SystemExit(1, x=2), "SystemExit"), (lambda: StopIteration(1, x=2), "StopIteration"),
                   (lambda: SyntaxError("m", x=2), "SyntaxError"), (lambda: Exception(x=1), "Exception"),
                   (lambda: UnicodeDecodeError("utf-8", b"x", 0, 1, "r", x=1), "UnicodeDecodeError"),
                   (lambda: ExceptionGroup("m", [ValueError()], x=1), "ExceptionGroup"),
                   (lambda: BaseExceptionGroup.__init__(ExceptionGroup("m", [ValueError()]), x=1), "ExceptionGroup"),
                   (lambda: OSError(x=1), "OSError"), (lambda: FileNotFoundError(2, "x", x=1), "FileNotFoundError")):
    assert_raises(TypeError, call, message=text + "() takes no keyword arguments")
assert_raises(TypeError, ImportError, "m", bad=1, message="ImportError() got an unexpected keyword argument 'bad'")
assert_is(OSError.__init__(OSError(), x=1), None)

# OSError.__init__ does nothing for a class OSError.__new__ parses for.
error = OSError()
OSError.__init__(error, 2, "x")
assert_eq((type(error), error.errno, error.args), (OSError, None, ()))

# A subclass whose own __init__ skips its base's leaves the attributes unset.
class Quiet(OSError):
    def __init__(self, *args): pass
error = Quiet(2, "x")
assert_eq((error.args, error.errno, error.strerror), ((), None, None))
class Forward(OSError):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs)
error = Forward(2, "x", "f")
assert_eq((type(error), error.args, error.errno, error.filename), (Forward, (2, "x"), 2, "f"))
assert_raises(TypeError, Forward, 2, x=1, message="Forward() takes no keyword arguments")
class Own(OSError):
    def __new__(cls, *args): return super().__new__(cls, *args)
    def __init__(self, *args): pass
assert_eq((Own(2, "x").args, Own(2, "x").errno), ((2, "x"), 2))
for cls, field in ((SystemExit, "code"), (StopIteration, "value"), (ImportError, "msg"), (SyntaxError, "msg")):
    Skip = type("Skip", (cls,), {"__init__": lambda self, *args: None})
    assert_is(getattr(Skip("m"), field), None, cls.__name__)

# ExceptionGroup is a class of builtins whose instances take weak references.
assert_eq(vars(ExceptionGroup)["__module__"], "builtins")
assert_eq(repr(vars(ExceptionGroup)["__weakref__"]), "<attribute '__weakref__'>")
assert_false("__weakref__" in vars(BaseExceptionGroup))
group = ExceptionGroup("m", [ValueError()])
assert_is(group.__weakref__, None)
assert_is(host.weak_reference(group)(), group)
assert_raises(AttributeError, lambda: ValueError().__weakref__)
class Sub(ExceptionGroup): pass
assert_false("__weakref__" in vars(Sub))
sub = Sub("m", [ValueError()])
assert_is(host.weak_reference(sub)(), sub)
