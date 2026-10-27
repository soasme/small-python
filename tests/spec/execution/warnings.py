# spec: PLS-315 18.3, B.4.1, 21.6
# description: Warnings reach HostWarn with a category, message and location; SyntaxWarning once per location.
from harness import *

def check(thunk, expected):
    """With HostWarn the warnings are as expected; without it they are ignored."""
    caught = host.warnings(thunk)
    if caught is not None:
        assert_eq(caught, expected)

# A compile-time warning carries the line of the construct.
check(lambda: compile("x = 1\nif x is 1:\n    pass\n", "<spec>", "exec"),
      [(SyntaxWarning, "\"is\" with 'int' literal. Did you mean \"==\"?", 2)])
# At most once per location per compilation.
check(lambda: compile("def f():\n    return 1 is 1\n", "<spec>", "exec"),
      [(SyntaxWarning, "\"is\" with 'int' literal. Did you mean \"==\"?", 2)])
check(lambda: compile("x = 1 is 1\ny = 2 is 2\n", "<spec>", "exec"),
      [(SyntaxWarning, "\"is\" with 'int' literal. Did you mean \"==\"?", 1),
       (SyntaxWarning, "\"is\" with 'int' literal. Did you mean \"==\"?", 2)])
# Invalid escape sequences warn; the string keeps the backslash.
check(lambda: compile("s = '\\d'\n", "<spec>", "exec"),
      [(SyntaxWarning, "\"\\d\" is an invalid escape sequence. Such sequences will not work in the future. "
        "Did you mean \"\\\\d\"? A raw string is also an option.", 1)])
assert_eq(eval("'\\d'"), "\\d")
# Shown, not raised: the program goes on.
assert_type(eval("1 is 1"), bool)  # whether it is True is implementation-defined (6.1.2)

# The categories are Warning subclasses and ordinary exceptions.
for category in (BytesWarning, DeprecationWarning, EncodingWarning, FutureWarning, ImportWarning,
                 PendingDeprecationWarning, ResourceWarning, RuntimeWarning, SyntaxWarning, UnicodeWarning, UserWarning):
    assert_eq(category.__bases__, (Warning,))
    assert_eq(category.__module__, "builtins")
    with assert_raises(category):
        raise category("raised")
assert_eq(Warning.__bases__, (Exception,))
