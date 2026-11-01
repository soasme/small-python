# spec: PLS-315 19.3.39, 17.5
# description: __lazy_import__ validates its name, level and fromlist before creating a lazy import object.
from harness import *

lazy = __lazy_import__
kind = type(lazy("no_such_module"))
assert_eq(kind.__name__, "lazy_import")
assert_raises(TypeError, lazy, 1, message="module name must be a string, got int")
assert_raises(ValueError, lazy, "m", level=-1, message="level must be >= 0")
assert_raises(TypeError, lazy, "m", level=1.5, message="'float' object cannot be interpreted as an integer")
for level in (2**40, 2**100):
    assert_raises(OverflowError, lazy, "m", level=level, message="Python int too large to convert to C int")
assert_raises(SyntaxError, lambda: lazy("m"), message="'lazy import' is only allowed at module level")

class Names(tuple): pass
class Name(str): pass
for fromlist in (None, (), "x", Name("x"), ("x", "y"), Names(("x",)), (Name("x"),)):
    assert_is(type(lazy("no_such_module", fromlist=fromlist)), kind)
# These checks follow the module-level one, so the calls are made at module level.
for fromlist, message in ((("x", 1), "Item in ``from list'' must be str, not int"),
                          (Names(("x", 1)), "Item in ``from list'' must be str, not int"),
                          (["x"], "lazy_import: fromlist must be None, a string, or a tuple"),
                          ({"x"}, "lazy_import: fromlist must be None, a string, or a tuple"),
                          (1, "lazy_import: fromlist must be None, a string, or a tuple")):
    try:
        lazy("m", fromlist=fromlist)
    except TypeError as error:
        assert_eq(str(error), message)
    else:
        fail(f"no TypeError for {fromlist!r}")

assert_eq(assert_raises(SyntaxError, compile, "from x lazy import y", "s", "exec").msg, "use 'lazy from ... ' instead of 'from ... lazy import'")
