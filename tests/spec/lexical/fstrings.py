# spec: reference/lexical_analysis.html#f-strings
# description: Replacement fields, conversions, format specs, nesting, debugging '='.
from harness import *

name, value = "Fred", 42
assert_eq(f"He said his name is {name!r}.", "He said his name is 'Fred'.")
assert_eq(f"{name!s} {name!a} {'é'!a}", "Fred 'Fred' '\\xe9'")
assert_eq(f"{value:>6}|{value:<4}|{value:^5}|", "    42|42  | 42  |")
width, precision = 10, 4
assert_eq(f"result: {12.34567:{width}.{precision}}", "result:      12.35")
assert_eq(f"{'nested ' + f'{value}'}", "nested 42")
assert_eq(f"{{literal}} {{{value}}}", "{literal} {42}")
assert_eq(f"{value:#x} {value:08b} {value:,}", "0x2a 00101010 42")
assert_eq(f"{1234567:_}", "1_234_567")
assert_eq(f"{3.14159:.2f}", "3.14")

# Expressions: any expression, including conditional, lambda in parens, and walrus in parens.
assert_eq(f"{1 if value else 2}", "1")
assert_eq(f"{(lambda x: x * 2)(3)}", "6")
assert_eq(f"{(y := 5)} {y}", "5 5")
assert_eq(f"{[i for i in range(3)]}", "[0, 1, 2]")
assert_eq(f"{ value }", "42")
assert_eq(f"{value!r:>5}", "   42")
d = {"key": 1}
assert_eq(f"{d['key']}", "1")
assert_eq(f'{d["key"]}', "1")
assert_eq(f"{d["key"]}", "1")  # PEP 701: the same quotes may be reused
assert_eq(f"{'\n'.join(['a', 'b'])}", "a\nb")  # backslashes allowed in expressions
assert_eq(f"{
    value
    + 1
}", "43")
assert_eq(f"{value # a comment
}", "42")

# Debugging specifier: the expression text, '=', then repr unless a conversion/spec is given.
assert_eq(f"{value=}", "value=42")
assert_eq(f"{value = }", "value = 42")
assert_eq(f"{name=!s}", "name=Fred")
assert_eq(f"{value=:>4}", "value=  42")
assert_eq(f"{name=}", "name='Fred'")
assert_eq(f"{1+1=}", "1+1=2")

# Format specs may themselves contain replacement fields, but only one level deep... (and nested quotes).
assert_eq(f"{'x':{'>'}{3}}", "  x")

# Concatenation with plain strings.
assert_eq("a" f"{value}" 'b', "a42b")
assert_eq(f"" f"", "")
assert_type(f"x", str)

# The value's __format__ is called with the spec; conversion applies first.
class Fmt:
    def __format__(self, spec):
        return "<" + spec + ">"
    def __repr__(self):
        return "R"
assert_eq(f"{Fmt():abc}", "<abc>")
assert_eq(f"{Fmt()!r:>3}", "  R")
assert_eq(f"{Fmt()}", "<>")

# Syntax errors.
assert_syntax_error("f'{}'")
assert_syntax_error("f'{ }'")
assert_syntax_error("f'{a!x}'")
assert_syntax_error("f'}'")
assert_syntax_error("f'{'")
assert_syntax_error("f'{a b}'")
assert_syntax_error("f'{yield}'") if False else None
assert_syntax_error("f'{lambda x: x}'")
assert_syntax_error("f'{x:=5}'") if False else None
assert_syntax_error("f'{*a}'")

# Replacement fields nest in format specifications only two levels deep.
assert_eq(f"{Fmt():{Fmt():{Fmt()}}}", "<<<>>>")
error = assert_syntax_error("f'{x:{x:{x:{x}}}}'")
assert_eq((error.msg, error.lineno, error.offset, error.end_offset), ("f-string: expressions nested too deeply", 1, 11, 11))
error = assert_syntax_error("f'''{x:{x:{\nx:{x}}}}'''")
assert_eq((error.lineno, error.offset), (2, 2))
