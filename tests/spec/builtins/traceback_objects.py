# spec: PLS-315 28.9, 18.1.3
# description: Traceback objects: attributes, tb_next assignment, and construction.
from harness import *

def raises():
    raise ValueError("x")
def calls():
    raises()
try:
    calls()
except ValueError as e:
    tb = e.__traceback__
TracebackType = type(tb)
assert_eq(TracebackType.__name__, "traceback")
assert_eq(tb.tb_frame.f_code.co_name, "<module>")
assert_eq(tb.tb_lineno, 10)
assert_eq(tb.tb_next.tb_lineno, 8)
assert_eq(tb.tb_next.tb_next.tb_lineno, 6)
assert_is(tb.tb_next.tb_next.tb_next, None)
assert_eq(type(tb.tb_lasti), int)
for name in ("tb_frame", "tb_lineno", "tb_lasti"):
    assert_raises(AttributeError, setattr, tb, name, None)

tb.tb_next = None
assert_is(tb.tb_next, None)
e = assert_raises(TypeError, setattr, tb, "tb_next", 1)
assert_eq(str(e), "expected traceback object, got 'int'")
try:
    raises()
except ValueError as e2:
    other = e2.__traceback__
tb.tb_next = other
e = assert_raises(ValueError, setattr, other, "tb_next", tb)
assert_eq(str(e), "traceback loop detected")
e = assert_raises(ValueError, setattr, tb, "tb_next", tb)
assert_eq(str(e), "traceback loop detected")

made = TracebackType(None, tb.tb_frame, 0, 42)
assert_eq((made.tb_lineno, made.tb_lasti, made.tb_next), (42, 0, None))
assert_is(made.tb_frame, tb.tb_frame)
chained = TracebackType(made, tb.tb_frame, 0, 1)
assert_is(chained.tb_next, made)
e = assert_raises(TypeError, TracebackType, 1, tb.tb_frame, 0, 1)
assert_eq(str(e), "expected traceback object or None, got 'int'")
e = assert_raises(TypeError, TracebackType, None, 1, 0, 1)
assert_eq(str(e), "traceback() argument 'tb_frame' must be frame, not int")
# with_traceback installs a constructed traceback.
error = KeyError().with_traceback(made)
assert_is(error.__traceback__, made)
