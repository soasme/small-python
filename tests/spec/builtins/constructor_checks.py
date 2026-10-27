# spec: PLS-315 19.2, 21.1.1, 21.3.5, 24.1.1
# description: T.__new__(S) argument checks, SyntaxError details, and bytes() encoding/errors pairing.
from harness import *

for new, cls, message in ((int.__new__, bool, "int.__new__(bool) is not safe, use bool.__new__()"),
                          (object.__new__, int, "object.__new__(int) is not safe, use int.__new__()"),
                          (tuple.__new__, int, "tuple.__new__(int): int is not a subtype of tuple"),
                          (bool.__new__, int, "bool.__new__(int): int is not a subtype of bool"),
                          (int.__new__, 1, "int.__new__(X): X is not a type object (int)"),
                          (BaseException.__new__, 1, "BaseException.__new__(X): X is not a type object (int)"),
                          (BaseException.__new__, int, "BaseException.__new__(int): int is not a subtype of BaseException")):
    assert_eq(str(assert_raises(TypeError, new, cls)), message)
assert_eq((bool.__new__(bool, 1), "__new__" in bool.__dict__), (True, True))
class Small(int): pass
assert_eq(type(int.__new__(Small, 5)), Small)

for details, message in (((1,), "function takes at least 4 arguments (1 given)"),
                         (tuple(range(8)), "function takes at most 7 arguments (8 given)"),
                         ((1, 2, 3, 4, 5), "end_offset must be provided when end_lineno is provided"),
                         (1, "'int' object is not iterable")):
    assert_eq(str(assert_raises(TypeError, SyntaxError, "m", details)), message)
e = SyntaxError("m", iter(["f", 1, 2, "t"]))
assert_eq((e.filename, e.lineno, e.offset, e.text, e.end_lineno, e.end_offset), ("f", 1, 2, "t", None, None))
e = SyntaxError("m", ("f", 1, 2, "t", 3, 4, None))
assert_eq((e.end_lineno, e.end_offset), (3, 4))

for kind in (bytes, bytearray):
    assert_eq(str(assert_raises(TypeError, kind, errors="strict")), "errors without a string argument")
    assert_eq(str(assert_raises(TypeError, kind, "a", errors="strict")), "string argument without an encoding")
    assert_eq(str(assert_raises(TypeError, kind, encoding="utf-8")), "encoding without a string argument")
assert_eq(str(b"a", errors="strict"), "a")
