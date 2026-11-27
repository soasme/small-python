# spec: PLS-315 12.5.4
# description: a concatenation's first literal of another kind than the one
# before it is the error. A t-string next to a literal of another kind is
# reported over the two; a bytes mix after the literals before the first
# t-string, at that t-string's prefix and quote or else the next token.
from harness import *

for source, message, at, end in [("x = b'a' 'b'", "cannot mix bytes and nonbytes literals", 13, 14),
                                 ("x = 'a' b'b' 'c' + 1", "cannot mix bytes and nonbytes literals", 18, 19),
                                 ("x = b'a' f'{1}' 'c'", "cannot mix bytes and nonbytes literals", 20, 21),
                                 ("f(b'a' 'b', 2)", "cannot mix bytes and nonbytes literals", 11, 12),
                                 ("x = 'a' b'b' t'c'", "cannot mix bytes and nonbytes literals", 14, 16),
                                 ("x = 'a' b'b' t'''c'''", "cannot mix bytes and nonbytes literals", 14, 18),
                                 ("x = b'a' 'b' rt'c'", "cannot mix bytes and nonbytes literals", 14, 17),
                                 ("x = t'a' 'b'", "cannot mix t-string literals with string or bytes literals", 5, 13),
                                 ("x = 'a' 'b' t'c' 'd' t'e'", "cannot mix t-string literals with string or bytes literals", 9, 17),
                                 ("x = t'a' t'b' b'c' 'd'", "cannot mix t-string literals with string or bytes literals", 10, 19),
                                 ("x = f'{1}' t'a'", "cannot mix t-string literals with string or bytes literals", 5, 16)]:
    caught = assert_syntax_error(source)
    assert_eq((caught.msg, caught.offset, caught.end_offset), (message, at, end), source)
caught = assert_syntax_error("x = (b'a'\n 'b')")
assert_eq((caught.lineno, caught.offset, caught.end_lineno, caught.end_offset), (2, 5, 2, 6))
caught = assert_syntax_error("x = (t'a'\n 'b')")
assert_eq((caught.lineno, caught.offset, caught.end_lineno, caught.end_offset), (1, 6, 2, 5))
assert_eq([b'a' b'b', 'a' f'{1}' 'c', (t'a' t'b').strings], [b'ab', 'a1c', ('ab',)])
