# spec: PLS-315 23.1.5
# description: split and rsplit by a separator count code points, from the left or the right, up to maxsplit.
from harness import *

text = "aéXbéXc"
assert_eq(text.split("éX"), ["a", "b", "c"])
assert_eq(text.rsplit("éX"), ["a", "b", "c"])
assert_eq(text.split("éX", 1), ["a", "béXc"])
assert_eq(text.rsplit("éX", 1), ["aéXb", "c"])
assert_eq("é,ü,,é".split(","), ["é", "ü", "", "é"])
assert_eq("é,ü,,é".rsplit(",", 2), ["é,ü", "", "é"])
assert_eq(b"x--y--z".rsplit(b"--", 1), [b"x--y", b"z"])
assert_eq(bytearray(b"x--y--z").split(b"--"), [bytearray(b"x"), bytearray(b"y"), bytearray(b"z")])
