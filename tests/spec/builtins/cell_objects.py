# spec: PLS-315 28.6, 9.1
# description: Cell objects: construction, contents, comparison, and repr.
from harness import *

def make():
    x = 1
    return (lambda: x).__closure__[0]
CellType = type(make())
assert_eq(CellType.__name__, "cell")
empty = CellType()
full = CellType(5)
assert_eq(full.cell_contents, 5)
e = assert_raises(ValueError, getattr, empty, "cell_contents")
assert_eq(str(e), "Cell is empty")
empty.cell_contents = 3
assert_eq(empty.cell_contents, 3)
del empty.cell_contents
assert_raises(ValueError, getattr, empty, "cell_contents")
assert_eq(CellType(), CellType())
assert_true(CellType() < CellType(0))
assert_eq(CellType(1), CellType(1))
assert_true(CellType(1) < CellType(2))
assert_raises(TypeError, hash, CellType(1))
assert_true(repr(empty).startswith("<cell at ") and repr(empty).endswith(": empty>"))
assert_true(": int object at " in repr(full))

# A cell of a closure writes through to the variable.
def counter():
    n = 0
    def get(): return n
    return get
get = counter()
get.__closure__[0].cell_contents = 9
assert_eq(get(), 9)
