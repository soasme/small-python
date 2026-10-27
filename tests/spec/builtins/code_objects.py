# spec: PLS-315 28.2, 6.2.7
# description: Code object attributes, flags, replace, line tables, equality, and immutability.
from harness import *

def sample(a, b, /, c, *args, d, e=1, **kwargs):
    """doc"""
    local = a
    def nested():
        return local
    return glob.attr

code = sample.__code__
assert_eq(type(code).__name__, "code")
assert_eq((code.co_name, code.co_qualname), ("sample", "sample"))
assert_true(code.co_filename.endswith("test_spec.py"))
assert_eq(code.co_firstlineno, 5)
assert_eq((code.co_argcount, code.co_posonlyargcount, code.co_kwonlyargcount), (3, 2, 2))
assert_eq(code.co_varnames[:7], ("a", "b", "c", "d", "e", "args", "kwargs"))
assert_eq(code.co_varnames[7:], ("nested",))
assert_eq(code.co_nlocals, len(code.co_varnames))
assert_eq(code.co_cellvars, ("local",))
assert_eq(code.co_freevars, ())
assert_eq(code.co_names, ("glob", "attr"))
assert_eq(code.co_consts[0], "doc")
def outer_of():
    local = 1
    def nested():
        return local
    return nested
inner = outer_of().__code__
assert_eq(inner.co_freevars, ("local",))
assert_eq(inner.co_qualname, "outer_of.<locals>.nested")
assert_true(inner.co_flags & 0x10)
flags = code.co_flags
assert_eq(flags & 0x03, 0x03)
assert_true(flags & 0x04 and flags & 0x08 and flags & 0x4000000)
assert_false(flags & 0x10)
def gen(): yield
async def coro(): pass
async def agen(): yield
assert_true(gen.__code__.co_flags & 0x20)
assert_true(coro.__code__.co_flags & 0x80)
assert_true(agen.__code__.co_flags & 0x200)
assert_false((lambda: 1).__code__.co_flags & 0x4000000)
assert_type(code.co_code, bytes)
assert_true(type(code.co_stacksize) is int and code.co_stacksize > 0)

e = assert_raises(AttributeError, setattr, code, "co_name", "x")
assert_eq(str(e), "readonly attribute")
renamed = code.replace(co_name="other")
assert_eq(renamed.co_name, "other")
assert_eq(code.co_name, "sample")
assert_eq(code.replace(), code)
assert_eq(hash(code.replace()), hash(code))
assert_ne(renamed, code)

# The ranges are consecutive and cover co_code from 0 (co_code itself is
# implementation-defined and may be empty).
lines = list(code.co_lines())
assert_true(all(len(triple) == 3 for triple in lines))
assert_eq(lines[0][0] if lines else 0, 0)
for (s1, e1, _), (s2, e2, _) in zip(lines, lines[1:]):
    assert_eq(e1, s2)
assert_eq(lines[-1][1] if lines else 0, len(code.co_code))
assert_true(all(len(p) == 4 for p in code.co_positions()))
assert_true(repr(code).startswith("<code object sample at "))
assert_true(repr(code).endswith(", line 5>"))
assert_true('file "' in repr(code))
