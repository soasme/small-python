# spec: library/stdtypes.html#common-sequence-operations
# description: Strings as sequences: indexing, slicing, and concatenation.
from harness import *
word = "Python"

assert "Python" == word[:2] + word[2:]
assert "Python" == word[:4] + word[4:]

assert "Py" == word[:2]
assert "on" == word[4:]
assert "on" == word[-2:]
assert "Py" == word[:-4]
# assert "Py" == word[::2]

assert "Pto" == word[::2]
assert "yhn" == word[1::2]
assert "Pt" == word[:4:2]
assert "yh" == word[1:4:2]
word = "Python"
assert "on" == word[4:42]
assert "" == word[42:]
word = "Python"

assert "Jython" == "J" + word[1:]
assert "Pypy" == word[:2] + "py"
s = "abcdefg"

assert 7 == len(s)
