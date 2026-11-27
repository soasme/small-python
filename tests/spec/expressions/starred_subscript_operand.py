# spec: PLS-315 13.3.2
# description: a subscript's starred item is a starred_expression, its
# operand any expression; it expands into the key tuple.
from harness import *

class K:
    def __getitem__(self, key): return key
    def __setitem__(self, key, value): self.set = (key, value)
    def __delitem__(self, key): self.deleted = key
k = K()
assert_eq(k[*[] or [1, 2]], (1, 2))
assert_eq(k[*(lambda: [3])()], (3,))
assert_eq(k[*[] if 0 else [4]], (4,))
assert_eq(k[0, *[] or [5], 6], (0, 5, 6))
assert_eq(k[1:2, *[7] and [8]], (slice(1, 2, None), 8))
k[*[] or [9]] = 10
del k[*[1] or []]
assert_eq((k.set, k.deleted), (((9,), 10), (1,)))
assert_eq(str(assert_raises(TypeError, lambda: k[*not []])), "Value after * must be an iterable, not bool")
for source, message, at, end in [("x[*yield]", "Invalid star expression", 4, 9), ("x[*]", "Invalid star expression", 4, 5), ("x[*a := 1]", "invalid syntax", 6, 8),
                                 ("x[*a:b]", "invalid syntax", 5, 6)]:
    caught = assert_syntax_error(source)
    assert_eq((caught.msg, caught.offset, caught.end_offset), (message, at, end), source)
