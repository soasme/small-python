# spec: PLS-315 16.7, 16.5, 14.12, 14.15
# description: type parameters that do not parse are invalid syntax where
# they fail, in a function definition "expected '('" at the "[" unless an
# expression among them ends there; a starred parameter's bound is an error
# from its colon over the bound; a decorator, a type statement's "=" and a
# lazy import's names are not forced.
from harness import *

for source, message, at, end in [("def f[T U](): pass", "expected '('", 6, 7), ("def f[1](): pass", "expected '('", 6, 7),
                                 ("def f[T = ](): pass", "expected '('", 6, 7), ("def f[*](): pass", "expected '('", 6, 7),
                                 ("def f[T: a b](): pass", "invalid syntax. Perhaps you forgot a comma?", 10, 13),
                                 ("def f[T: x if y](): pass", "expected 'else' after 'if' expression", 10, 16),
                                 ("class C[T U]: pass", "invalid syntax", 11, 12), ("type X[T] 1", "invalid syntax", 11, 12),
                                 ("type X[T]", "invalid syntax", 10, 11),
                                 ("def f[*Ts: int | str](): pass", "cannot use bound with TypeVarTuple", 10, 21),
                                 ("def f[**P: (a, b)](): pass", "cannot use constraints with ParamSpec", 10, 18),
                                 ("class C[**P: int]: pass", "cannot use bound with ParamSpec", 12, 17),
                                 ("type X[*Ts: (int,)] = 1", "cannot use constraints with TypeVarTuple", 11, 19),
                                 ("@a b\ndef f(): pass", "invalid syntax", 4, 5), ("@a.b c", "invalid syntax", 6, 7),
                                 ("lazy import\n", "invalid syntax", 12, 13), ("import\n", "Expected one or more names after 'import'", 7, 7)]:
    caught = assert_syntax_error(source)
    assert_eq((caught.msg, caught.offset, caught.end_offset), (message, at, end), source)
