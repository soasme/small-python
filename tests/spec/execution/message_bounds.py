# spec: PLS-315 5.2.6, 7.3.5, 7.3.6, 7.3.8, 7.6.2, 7.6.3, 9.3.2, 22.1.2, 22.3.1, 24.3, 8.3.1
# description: Exception messages carry their substitutions in full, however long, except where a bound cuts one to a number of UTF-8 bytes, never splitting a character.
from harness import *

long = "a" * 400
wide = "é" * 300  # two bytes a character

# Unbounded substitutions appear in full; the name attributes keep the whole name.
error = assert_raises(AttributeError, getattr, object(), long)
assert_eq(str(error), "'object' object has no attribute '" + long + "'")
assert_eq(error.name, long)
error = assert_raises(ModuleNotFoundError, __import__, long)
assert_eq(str(error), "No module named '" + long + "'")
assert_eq(error.name, long)
assert_raises(ValueError, float, long, message="could not convert string to float: '" + long + "'")
assert_raises(ValueError, float, wide, message="could not convert string to float: '" + wide + "'")
def f():
    pass
assert_raises(TypeError, f, **{long: 1}, message="f() got an unexpected keyword argument '" + long + "'")
error = assert_raises(SyntaxError, compile, "def f(" + long + ", " + long + "): pass", "<s>", "exec")
assert_eq(error.msg, "duplicate parameter '" + long + "' in function definition")

# An undefined name shows at most 200 bytes of itself.
error = assert_raises(NameError, eval, long)
assert_eq(str(error), "name '" + "a" * 200 + "' is not defined")
assert_eq(error.name, long)
assert_raises(NameError, eval, wide, message="name '" + "é" * 100 + "' is not defined")
assert_raises(NameError, eval, "a" + wide, message="name '" + "a" + "é" * 99 + "' is not defined")

# int() shows 200 characters of the text, whatever their width.
assert_raises(ValueError, int, wide, message="invalid literal for int() with base 10: '" + "é" * 199)

# Type names in attribute and operator errors show at most 100 bytes.
Long = type("N" * 150, (), {})
Wide = type("é" * 80, (), {})
cut = "N" * 100
assert_raises(AttributeError, lambda: Long().x, message="'" + cut + "' object has no attribute 'x'")
assert_raises(AttributeError, lambda: Wide().x, message="'" + "é" * 50 + "' object has no attribute 'x'")
assert_raises(AttributeError, lambda: Long.x, message="type object '" + cut + "' has no attribute 'x'")
def delete():
    del Long().x
assert_raises(AttributeError, delete, message="'" + cut + "' object has no attribute 'x'")
assert_raises(TypeError, lambda: Long() + 1, message="unsupported operand type(s) for +: '" + cut + "' and 'int'")
assert_raises(TypeError, lambda: pow(1, Long(), 2), message="unsupported operand type(s) for ** or pow(): 'int', '" + cut + "', 'int'")
assert_raises(TypeError, divmod, Long(), 1, message="unsupported operand type(s) for divmod(): '" + cut + "' and 'int'")
def augmented():
    x = Long()
    x -= 1
assert_raises(TypeError, augmented, message="unsupported operand type(s) for -=: '" + cut + "' and 'int'")
assert_raises(TypeError, lambda: b"" + Long(), message="can't concat " + cut + " to bytes")
