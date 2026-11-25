# spec: PLS-315 14.2.2, 14.7, 15.3
# description: An empty target list, alone or among other targets, unpacks
# an iterable that must yield no items; deleting one deletes nothing. The
# targets around it are stored or deleted in order, in function and module
# bodies alike, and as a for statement's target.
from harness import *

class O: pass

def run():
    o = O(); o.b = 1; d = {0: 1}; a = 1
    () = []
    [] = ()
    x, () = 1, []
    o.c, [] = 3, ""
    del a, (), o.b
    del (), [], d[0]
    del ()
    seen = 0
    for () in [(), [], ""]: seen += 1
    for o.e, () in [(5, ())]: pass
    return x, o.c, o.e, hasattr(o, "b"), d, seen

assert_eq(run(), (1, 3, 5, False, {}, 3))
o = O(); o.b = 1; a = 1
() = []
x, () = 1, []
del a, (), o.b
assert_eq((x, hasattr(o, "b"), "a" in globals()), (1, False, False))
assert_eq(str(assert_raises(ValueError, exec, "() = [1]")), "too many values to unpack (expected 0, got 1)")
assert_eq(str(assert_raises(TypeError, exec, "o.e, () = 1, 2", {"o": o})), "cannot unpack non-iterable int object")
assert_eq(hasattr(o, "e"), True)
