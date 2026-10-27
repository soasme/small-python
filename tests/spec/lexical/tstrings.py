# spec: reference/lexical_analysis.html#t-strings
# description: Template string literals evaluate to string.templatelib.Template objects.
from harness import *

name = "World"
t = t"Hello {name}!"
assert_eq(type(t).__name__, "Template")
assert_eq(t.strings, ("Hello ", "!"))
assert_eq(len(t.interpolations), 1)
i = t.interpolations[0]
assert_eq(type(i).__name__, "Interpolation")
assert_eq((i.value, i.expression, i.conversion, i.format_spec), ("World", "name", None, ""))
assert_eq(t.values, ("World",))
assert_eq(list(t), ["Hello ", i, "!"])

t = t"{name!r:>10} and {1 + 2 = }"
a, b = t.interpolations
assert_eq((a.value, a.expression, a.conversion, a.format_spec), ("World", "name", "r", ">10"))
assert_eq((b.value, b.expression, b.conversion), (3, "1 + 2 ", "r"))
assert_eq(t.strings, ("", " and 1 + 2 = ", ""))

# Format specs are evaluated eagerly but not applied.
width = 5
t = t"{name:{width}}"
assert_eq(t.interpolations[0].format_spec, "5")

# Adjacent t-strings concatenate; mixing with str or bytes literals is an error.
t = t"a{name}" t"b"
assert_eq(t.strings, ("a", "b"))
assert_syntax_error("t'a' 'b'")
assert_syntax_error("'a' t'b'")
assert_syntax_error("t'a' f'b'")
assert_syntax_error("t'a' b'b'")

# Raw t-strings keep backslashes.
assert_eq(rt"\n{name}".strings, ("\\n", ""))
assert_eq(t"".strings, ("",))
assert_eq(t"{name}{name}".strings, ("", "", ""))

# Templates are not strings and support +.
assert_false(isinstance(t"x", str))
joined = t"a{name}" + t"b{width}"
assert_eq(joined.strings, ("a", "b", ""))
assert_raises(TypeError, lambda: t"a" + "b")
