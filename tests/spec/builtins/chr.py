# spec: PLS-315 19.3.9
# description: chr() and its range and argument errors.
from harness import *

assert "a" == chr(97)
assert "é" == chr(233)
assert "🤡" == chr(129313)

assert_raises(TypeError, chr)
assert_raises(
    ValueError, chr, 0x110005
)
