# spec: PLS-315 19.3.6
# description: hex() of ints and __index__ objects.
from harness import *

assert hex(16) == "0x10"
assert hex(-16) == "-0x10"

assert_raises(TypeError, hex, {})
