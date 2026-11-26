# spec: PLS-315 18.2.3
# description: f-strings and t-strings nested in one another's
# replacement fields beyond the implementation's limit raise SyntaxError
# "too many nested f-strings or t-strings", for either kind; a few
# levels compile. An expression too deep for the compiler raises
# RecursionError ("Stack overflow (used n kB) during compilation") or
# MemoryError, and does not crash.
from harness import *

def nested(levels, prefix="f"):
    quotes = ["'", '"', "'''", '"""']
    source = "1"
    for i in range(levels):
        source = prefix + quotes[i % 4] + "{" + source + "}" + quotes[i % 4]
    return source

assert_eq(eval(nested(4)), "1")
assert_eq(type(eval(nested(3, "t"))).__name__, "Template")
for source in (nested(200), nested(200, "t"), "f'{" + nested(199, "t") + "}'"):
    error = assert_syntax_error(source, mode="eval")
    assert_eq((type(error), error.msg), (SyntaxError, "too many nested f-strings or t-strings"))

def stack_message(text):
    head, _, tail = text.partition("Stack overflow (used ")
    count, _, rest = tail.partition(" kB) during compilation")
    return head == "" and count.isdigit() and rest == ""

for source in ("-" * 10000 + "1", "-" * 100000 + "1", "not " * 100000 + "1"):
    try:
        compile(source, "m", "eval")
        fail("compiled")
    except RecursionError as error:
        assert_true(stack_message(str(error)), str(error))
    except MemoryError as error:
        assert_eq(str(error), "Parser stack overflowed - Python source too complex to parse")
