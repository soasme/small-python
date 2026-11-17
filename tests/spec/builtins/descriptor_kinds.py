# spec: PLS-315 28.7, 28.8
# description: bytes.__bytes__ is a method descriptor, bound as a builtin
# method; a coroutine's cr_origin and an asynchronous generator's
# ag_running are read-only member descriptors, their other attributes
# getset descriptors. Inside functions as at module level.
from harness import *

async def co(): pass
async def ag(): yield

def kinds():
    c = co(); c.close()
    C, A = type(c), type(ag())
    kind = lambda t, n: type(vars(t)[n]).__name__
    out = [kind(bytes, "__bytes__"), type(b"x".__bytes__).__name__, b"x".__bytes__(), kind(C, "cr_origin"), kind(A, "ag_running"),
           kind(C, "cr_running"), kind(A, "ag_frame"), repr(vars(C)["cr_origin"]), c.cr_origin]
    out.append(str(assert_raises(AttributeError, setattr, c, "cr_origin", 1)))
    return out

expected = ["method_descriptor", "builtin_function_or_method", b"x", "member_descriptor", "member_descriptor",
            "getset_descriptor", "getset_descriptor", "<member 'cr_origin' of 'coroutine' objects>", None,
            "readonly attribute"]

def main():
    return kinds()

assert_eq(main(), expected)
assert_eq(kinds(), expected)
