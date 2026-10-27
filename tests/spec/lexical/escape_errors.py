# spec: PLS-315 12.5.3
# description: A faulty escape names its codec, position and reason; positions count non-ASCII code points as ten.
from harness import *
for source, message in (
        (r"'\x1'", "(unicode error) 'unicodeescape' codec can't decode bytes in position 0-2: truncated \\xXX escape"),
        (r"'ab\u12'", "(unicode error) 'unicodeescape' codec can't decode bytes in position 2-5: truncated \\uXXXX escape"),
        (r"'\U0011ffff'", "(unicode error) 'unicodeescape' codec can't decode bytes in position 0-9: illegal Unicode character"),
        (r"'\U001'", "(unicode error) 'unicodeescape' codec can't decode bytes in position 0-4: truncated \\UXXXXXXXX escape"),
        (r"'\N{no such name}'", "(unicode error) 'unicodeescape' codec can't decode bytes in position 0-15: unknown Unicode character name"),
        (r"'\N'", "(unicode error) 'unicodeescape' codec can't decode bytes in position 0-1: malformed \\N character escape"),
        ("'é\\x1'", "(unicode error) 'unicodeescape' codec can't decode bytes in position 10-12: truncated \\xXX escape"),
        (r"f'{1}ab\x1'", "(unicode error) 'unicodeescape' codec can't decode bytes in position 2-4: truncated \\xXX escape"),
        (r"b'a\x1'", "(value error) invalid \\x escape at position 1")):
    assert_eq(assert_syntax_error(source).msg, message)
# The error is reported on the line where the literal begins.
assert_eq(assert_syntax_error("x = '\\\n\\x1'").lineno, 1)
