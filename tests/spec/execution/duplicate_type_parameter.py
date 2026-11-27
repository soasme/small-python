# spec: PLS-315 8.3.1, 16.7
# description: a type parameter list naming one parameter twice is a
# SyntaxError reported over the whole repeated parameter: its star or
# double star, its name, and its bound and default.
from harness import *

def extent(source):
    caught = assert_syntax_error(source)
    return caught.msg, caught.lineno, caught.offset, caught.end_lineno, caught.end_offset

assert_eq(extent("def f[T, T](): pass"), ("duplicate type parameter 'T'", 1, 10, 1, 11))
assert_eq(extent("class C[T, *T]: pass"), ("duplicate type parameter 'T'", 1, 12, 1, 14))
assert_eq(extent("type A[T, **T] = int"), ("duplicate type parameter 'T'", 1, 11, 1, 14))
assert_eq(extent("def f[T, U, T](): pass"), ("duplicate type parameter 'T'", 1, 13, 1, 14))
assert_eq(extent("def f[T, T: int](): pass"), ("duplicate type parameter 'T'", 1, 10, 1, 16))
assert_eq(extent("def f[T, T = int](): pass"), ("duplicate type parameter 'T'", 1, 10, 1, 17))
assert_eq(extent("type A[T, T: (int, str)] = int"), ("duplicate type parameter 'T'", 1, 11, 1, 24))
assert_eq(extent("class C[**P, *P]: pass"), ("duplicate type parameter 'P'", 1, 14, 1, 16))
assert_eq(extent("def f[\n    T,\n    T,\n](): pass"), ("duplicate type parameter 'T'", 3, 5, 3, 6))
assert_eq(extent("def o():\n    x = 0\n    class C[T, T]: pass"), ("duplicate type parameter 'T'", 3, 16, 3, 17))
# The spelling is the second parameter's, the comparison after normalization.
assert_eq(extent("def f[ﬁ, fi](): pass"), ("duplicate type parameter 'fi'", 1, 12, 1, 14))
