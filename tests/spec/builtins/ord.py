# spec: PLS-315 19.3.29
# description: ord() of str, bytes, and bytearray, and its length errors.
from harness import *

assert ord("a") == 97
assert ord("é") == 233
assert ord("🤡") == 129313
assert ord(b"a") == 97
assert ord(bytearray(b"a")) == 97

assert_raises(TypeError, ord)
assert_raises(TypeError, ord, "")
assert_raises(TypeError, ord, "ab")
assert_raises(
    TypeError,
    ord,
    b"ab",
)
assert_raises(
    TypeError, ord, 1
)
