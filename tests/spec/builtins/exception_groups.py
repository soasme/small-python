# spec: PLS-315 21.4, 15.4.3
# description: BaseExceptionGroup construction, derive, split, and subgroup.
from harness import *

g = BaseExceptionGroup("msg", [ValueError(1), TypeError(2)])
assert_type(g, ExceptionGroup)
assert_eq(g.message, "msg")
assert_type(g.exceptions, tuple)
assert_eq([type(x) for x in g.exceptions], [ValueError, TypeError])
assert_eq(g.args[0], "msg")
assert_eq(str(g), "msg (2 sub-exceptions)")
assert_eq(str(ExceptionGroup("one", [ValueError()])), "one (1 sub-exception)")
assert_eq(repr(ExceptionGroup("m", [ValueError(1)])), "ExceptionGroup('m', [ValueError(1)])")
assert_type(BaseExceptionGroup("m", [KeyboardInterrupt()]), BaseExceptionGroup)
assert_raises(AttributeError, setattr, g, "message", "x")
assert_raises(AttributeError, setattr, g, "exceptions", ())

e = assert_raises(TypeError, BaseExceptionGroup, "m")
assert_eq(str(e), "BaseExceptionGroup.__new__() takes exactly 2 arguments (1 given)")
e = assert_raises(TypeError, BaseExceptionGroup, 1, [ValueError()])
assert_eq(str(e), "BaseExceptionGroup.__new__() argument 1 must be str, not int")
e = assert_raises(TypeError, BaseExceptionGroup, "m", {ValueError()})
assert_eq(str(e), "second argument (exceptions) must be a sequence")
e = assert_raises(ValueError, BaseExceptionGroup, "m", [])
assert_eq(str(e), "second argument (exceptions) must be a non-empty sequence")
e = assert_raises(ValueError, BaseExceptionGroup, "m", [ValueError(), 1])
assert_eq(str(e), "Item 1 of second argument (exceptions) is not an exception")
e = assert_raises(TypeError, ExceptionGroup, "m", [KeyboardInterrupt()])
assert_eq(str(e), "Cannot nest BaseExceptions in an ExceptionGroup")
class MyGroup(ExceptionGroup):
    pass
e = assert_raises(TypeError, MyGroup, "m", [KeyboardInterrupt()])
assert_eq(str(e), "Cannot nest BaseExceptions in 'MyGroup'")

# derive does not keep a subclass.
mine = MyGroup("m", [ValueError()])
assert_type(mine.derive([TypeError()]), ExceptionGroup)
assert_type(mine.derive([KeyboardInterrupt()]), BaseExceptionGroup)

# split and subgroup.
inner = ExceptionGroup("inner", [KeyError("k"), ValueError("v2")])
g = ExceptionGroup("outer", [ValueError("v1"), TypeError("t"), inner])
g.__notes__ = ["note"]
g.__cause__ = RuntimeError("cause")
match, rest = g.split(ValueError)
assert_eq(str(match), "outer (2 sub-exceptions)")
assert_eq([type(x) for x in match.exceptions], [ValueError, ExceptionGroup])
assert_eq([type(x) for x in match.exceptions[1].exceptions], [ValueError])
assert_eq([type(x) for x in rest.exceptions], [TypeError, ExceptionGroup])
assert_eq(match.__notes__, ["note"])
assert_true(match.__notes__ is not g.__notes__)
assert_is(match.__cause__, g.__cause__)
# With no match, the rest is a derived copy, not the group itself.
none, rest = g.split(OSError)
assert_is(none, None)
assert_true(rest is not g)
assert_eq([type(x) for x in rest.exceptions], [ValueError, TypeError, ExceptionGroup])
assert_is(g.split(Exception)[0], g)
assert_is(g.subgroup(Exception), g)
assert_eq(g.subgroup(OSError), None)
assert_eq([type(x) for x in g.subgroup((TypeError, KeyError)).exceptions], [TypeError, ExceptionGroup])
assert_eq([type(x) for x in g.subgroup(lambda x: isinstance(x, KeyError)).exceptions], [ExceptionGroup])
# The predicate also sees the groups themselves.
assert_is(g.subgroup(lambda x: x is g), g)
e = assert_raises(TypeError, g.split, 1)
assert_eq(str(e), "expected an exception type, a tuple of exception types, or a callable (other than a class)")
assert_raises(TypeError, g.split, int)
# derive must return a group.
class BadDerive(ExceptionGroup):
    def derive(self, excs):
        return 1
e = assert_raises(TypeError, BadDerive("m", [ValueError(), TypeError()]).split, ValueError)
assert_eq(str(e), "derive must return an instance of BaseExceptionGroup")
