# spec: PLS-315 20.8
# description: sentinel objects: unique markers with a name, a repr, the caller's module, and reduction by name.
from harness import *

MISSING = sentinel("MISSING")
assert_eq(MISSING.__name__, "MISSING")
assert_eq(MISSING.__module__, __name__)
assert_eq(repr(MISSING), "MISSING")
assert_eq(MISSING.__repr__(), "MISSING")
custom = sentinel("X", repr="<custom>")
assert_eq(repr(custom), "<custom>")
assert_eq(custom.__name__, "X")
assert_true(MISSING)
assert_eq(MISSING, MISSING)
assert_ne(MISSING, sentinel("MISSING"))
assert_eq(hash(MISSING), hash(MISSING))
assert_eq({MISSING: 1}[MISSING], 1)
assert_eq(MISSING.__reduce__(), "MISSING")
assert_false(hasattr(MISSING, "__dict__"))
assert_raises(AttributeError, setattr, MISSING, "x", 1)
assert_type(MISSING, sentinel)

e = assert_raises(TypeError, sentinel, 1)
assert_eq(str(e), "sentinel() argument 1 must be str, not int")
e = assert_raises(TypeError, sentinel, "a", repr=1)
assert_eq(str(e), "sentinel() argument 'repr' must be str or None, not int")
e = assert_raises(TypeError, sentinel)
assert_eq(str(e), "sentinel() takes exactly 1 positional argument (0 given)")
e = assert_raises(TypeError, sentinel, "a", "b")
assert_eq(str(e), "sentinel() takes exactly 1 positional argument (2 given)")
assert_raises(TypeError, sentinel, "a", other=1)
assert_eq(repr(sentinel("a", repr=None)), "a")
with assert_raises(TypeError):
    class Sub(sentinel):
        pass
# Created from code run in another namespace, __module__ is that namespace's __name__.
ns = run("s = sentinel('S')\n", {"__name__": "elsewhere"})
assert_eq(ns["s"].__module__, "elsewhere")
