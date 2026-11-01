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

# Every word of the name exists, but no character has this name.
error = assert_syntax_error('"\\N{LATIN LETTER SMALL}"')
assert_eq(error.msg, "(unicode error) 'unicodeescape' codec can't decode bytes in position 0-21: unknown Unicode character name")

# In an f- or t-string, the position counts within the text segment holding
# the escape, and the error spans that segment. A segment ends before a
# field, after the first of a doubled brace, or after a \N{...} escape.
for source, position, location in (
        (r'f"\xZZ"', "0-1", (1, 3, 1, 7)),
        (r'f"ab{x!r}cd\xZZ"', "2-3", (1, 10, 1, 16)),
        (r'f"a{{b\xZZc"', "1-2", (1, 6, 1, 12)),
        (r'f"\xZZ}}c{x}"', "0-1", (1, 3, 1, 9)),
        (r'f"\xZZ\N{DASH}x{y}"', "0-1", (1, 3, 1, 15)),
        (r'f"\N{EM DASH}\xZZ"', "0-1", (1, 14, 1, 18)),
        (r't"{x}\xZZ"', "0-1", (1, 6, 1, 10)),
        ('f"""abc\n{x}\\xZZ\ndef"""', "0-1", (2, 4, 3, 4)),
        (r'"ok" f"\xZZ"', "0-1", (1, 8, 1, 12))):
    error = assert_syntax_error(source)
    assert_eq(error.msg, f"(unicode error) 'unicodeescape' codec can't decode bytes in position {position}: truncated \\xXX escape")
    assert_eq((error.lineno, error.offset, error.end_lineno, error.end_offset), location)

# A literal that ends on a later line reports its end column measured
# against the first line: at most that line's length, plus one.
for source, location in (
        ('"""a\n\\xZZ"""', (1, 1, 2, 5)),
        ('"""abcdefgh\n\\xZZ"""', (1, 1, 2, 8)),
        ('x = """a\n\\xZZ"""', (1, 5, 2, 8)),
        ('"""é\n\\xZZ"""', (1, 1, 2, 5)),
        ('"a\\\n\\xZZ"', (1, 1, 2, 4))):
    error = assert_syntax_error(source)
    assert_eq((error.lineno, error.offset, error.end_lineno, error.end_offset), location)
