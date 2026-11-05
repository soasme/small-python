# spec: PLS-315 21.1.1, 21.1.3, 21.1.6
# description: BaseException's __repr__, __str__ and __dict__, the subclasses' own __str__, __repr__ and __new__, and str() and repr() calling them through the type.
from harness import *

# The methods live on the classes that define them.
for cls, names in ((BaseException, ("__new__", "__repr__", "__str__", "__dict__")), (Exception, ("__new__",)),
                   (ValueError, ("__new__",)), (LookupError, ("__new__",)), (KeyError, ("__str__",)),
                   (OSError, ("__new__", "__str__")), (ImportError, ("__repr__", "__str__")), (SyntaxError, ("__str__",)),
                   (UnicodeDecodeError, ("__new__", "__str__"))):
    for name in names:
        assert_true(name in vars(cls), f"{cls.__name__}.{name}")
for cls, name in ((Exception, "__repr__"), (Exception, "__str__"), (KeyError, "__new__"), (StopIteration, "__new__"),
                  (FileNotFoundError, "__new__"), (FileNotFoundError, "__str__"), (ExceptionGroup, "__new__"), (ValueError, "__dict__")):
    assert_false(name in vars(cls), f"{cls.__name__}.{name}")
assert_true(Exception.__new__ is not BaseException.__new__)
assert_true(ValueError.__repr__ is BaseException.__repr__ and KeyError.__new__ is LookupError.__new__)

# A method called through a class formats as that class does.
assert_eq(BaseException.__repr__(ValueError(1, 2)), "ValueError(1, 2)")
assert_eq(BaseException.__str__(KeyError("k")), "k")
assert_eq(KeyError.__str__(KeyError("k")), "'k'")
assert_eq(BaseException.__str__(OSError(2, "gone", "f")), "(2, 'gone')")
assert_eq(OSError.__str__(OSError(2, "gone", "f")), "[Errno 2] gone: 'f'")
error = ImportError("m", name="n", path="p")
assert_eq((str(error), repr(error), BaseException.__repr__(error)), ("m", "ImportError('m', name='n', path='p')", "ImportError('m')"))
assert_eq(BaseException.__str__(SyntaxError("bad", ("f.py", 3, 1, "x"))), "('bad', ('f.py', 3, 1, 'x'))")
assert_eq(str(SyntaxError("bad", ("f.py", 3, 1, "x"))), "bad (f.py, line 3)")
assert_eq(str(UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad")), "'utf-8' codec can't decode byte 0xff in position 0: bad")
assert_eq((str(ValueError()), str(ValueError(1)), str(ValueError(1, 2)), repr(ValueError())), ("", "1", "(1, 2)", "ValueError()"))

# str() and repr() call the method the type finds, so super() reaches the base's.
class Key(KeyError):
    def __str__(self):
        return "<" + super().__str__() + ">"
class Quiet(ValueError):
    def __repr__(self):
        return "Quiet!"
assert_eq((str(Key("x")), repr(Key("x")), f"{Key('x')}"), ("<'x'>", "Key('x')", "<'x'>"))
assert_eq((repr(Quiet(1)), str(Quiet(1)), BaseException.__repr__(Quiet(1))), ("Quiet!", "1", "Quiet(1)"))
assert_eq(KeyError("k").__str__(), "'k'")

# Each method checks its receiver and takes no other argument.
assert_raises(TypeError, BaseException.__repr__, message="descriptor '__repr__' of 'BaseException' object needs an argument")
assert_raises(TypeError, BaseException.__str__, 1, message="descriptor '__str__' requires a 'BaseException' object but received a 'int'")
assert_raises(TypeError, KeyError.__str__, ValueError(), message="descriptor '__str__' requires a 'KeyError' object but received a 'ValueError'")
assert_raises(TypeError, BaseException.__str__, ValueError(), 2, message="expected 0 arguments, got 1")
assert_raises(TypeError, BaseException.__repr__, ValueError(), k=1, message="wrapper __repr__() takes no keyword arguments")

# A class's own __new__ names it and allocates only what it may.
assert_eq(type(Exception.__new__(KeyError, 1)), KeyError)
assert_eq(Exception.__new__(ValueError, 1, 2).args, (1, 2))
assert_eq(type(BaseException.__new__(SystemExit, 3)), SystemExit)
assert_raises(TypeError, Exception.__new__, message="Exception.__new__(): not enough arguments")
assert_raises(TypeError, Exception.__new__, 1, message="Exception.__new__(X): X is not a type object (int)")
assert_raises(TypeError, KeyError.__new__, int, message="LookupError.__new__(int): int is not a subtype of LookupError")
assert_raises(TypeError, ValueError.__new__, KeyError, message="ValueError.__new__(KeyError): KeyError is not a subtype of ValueError")
assert_raises(TypeError, Exception.__new__, OSError, 2, "x", message="Exception.__new__(OSError) is not safe, use OSError.__new__()")
assert_raises(TypeError, Exception.__new__, ExceptionGroup, "m", [ValueError()],
              message="Exception.__new__(ExceptionGroup) is not safe, use ExceptionGroup.__new__()")
class Made(Exception):
    def __new__(cls, *args):
        return super().__new__(cls, *args)
assert_eq(Made(5).args, (5,))

# __dict__ is a getset of BaseException: the instance namespace.
descriptor = vars(BaseException)["__dict__"]
assert_eq(repr(descriptor), "<attribute '__dict__' of 'BaseException' objects>")
error = ValueError(3)
error.x = 1
assert_eq(descriptor.__get__(error), {"x": 1})
error.__dict__ = {"y": 2}
assert_eq((error.y, vars(error)), (2, {"y": 2}))
assert_raises(TypeError, delattr, error, "__dict__", message="cannot delete __dict__")
assert_raises(TypeError, descriptor.__get__, 1, message="descriptor '__dict__' for 'BaseException' objects doesn't apply to a 'int' object")
