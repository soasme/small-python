# spec: PLS-315 A.5, 16.1, 16.7
# description: The definition grammar of Annex A: decorators, parameter lists, and type parameters.
from harness import *

# decorators: ('@' named_expression NEWLINE)+
assert_compiles("@a\n@b.c(1)[2]\n@(x := d)\n@e if f else g\ndef h(): pass\n")
assert_compiles("@a\nclass C: pass\n")
assert_syntax_error("@a\nx = 1\n")
assert_syntax_error("@a, b\ndef h(): pass\n")
assert_syntax_error("@*a\ndef h(): pass\n")

# class_def_raw
for source in ("class C: pass", "class C(): pass", "class C(A, B, metaclass=M, **k): pass",
               "class C(*bases): pass", "class C[T]: pass", "class C[T](A): pass"):
    assert_compiles(source + "\n")
assert_syntax_error("class C[]: pass\n")
assert_syntax_error("class C(): -> int: pass\n")

# function_def_raw and params
valid = [
    "def f(): pass",
    "def f(a, /): pass",
    "def f(a, /, b, c=1, *, d, e=2, **k): pass",
    "def f(a=1, /, b=2): pass",
    "def f(a, b=1, /, c=2, *d, e, **f): pass",
    "def f(*, a): pass",
    "def f(*a, b=1, c): pass",
    "def f(**k,): pass",
    "def f(a: int, *b: str, **c: bytes) -> None: pass",
    "def f(*a: *Ts): pass",
    "def f[T, *Ts, **P](a: T) -> T: pass",
    "async def f(a, /): pass",
]
for source in valid:
    assert_compiles(source + "\n")
invalid = [
    "def f(a=1, b): pass",          # a parameter without a default after one with
    "def f(a=1, /, b): pass",
    "def f(/): pass",               # '/' needs a parameter before it
    "def f(a, /, /): pass",
    "def f(*, /): pass",
    "def f(*): pass",               # bare '*' needs a keyword-only parameter
    "def f(*, **k): pass",
    "def f(*a, *b): pass",
    "def f(**k, a): pass",
    "def f(**k=1): pass",
    "def f(*a=1): pass",
    "def f(a: *b): pass",           # star_annotation only for *args
    "def f(**k: *b): pass",
    "def f(a, a): pass",
    "def f() -> *T: pass",
    "async lambda: 1",
]
for source in invalid:
    assert_syntax_error(source + "\n")

# type_params, type_param_bound, and the defaults.
for source in ("type A = int", "type A[T] = T", "type A[T: int, *Ts, **P,] = T",
               "type A[T = int, *Ts = *tuple[int], **P = [int]] = T", "def f[T: (int, str) = int](): pass",
               "type A[*Ts = *Ts2] = 0"):
    assert_compiles(source + "\n")
for source in ("type A[] = int", "type A[*Ts: int] = 0", "type A[**P: int] = 0",
               "type A = *b", "type A[T = *b] = 0", "type A[**P = *b] = 0", "type A[T] = int = str",
               "type A[T = int, U] = 0"):
    assert_syntax_error(source + "\n")
