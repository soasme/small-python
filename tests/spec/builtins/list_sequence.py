# spec: PLS-315 25.1, 25.5, 25.5.2
# description: Lists as sequences: indexing, slicing, concatenation, and mutation.
from harness import *
squares = [1, 4, 9, 16, 25]

assert 1 == squares[0]
assert 25 == squares[-1]
assert [9, 16, 25] == squares[-3:]
assert squares == squares[:]

assert [1, 9, 25] == squares[::2]
assert [4, 16] == squares[1::2]
assert [4] == squares[1:2:2]
assert [25] == squares[4:100]

squares_tuple = (1, 4, 9, 16, 25)

assert 1 == squares_tuple[0]
assert 25 == squares_tuple[-1]
assert (9, 16, 25) == squares_tuple[-3:]
assert squares_tuple == squares_tuple[:]

assert (1, 9, 25) == squares_tuple[::2]
assert (4, 16) == squares_tuple[1::2]
assert (4,) == squares_tuple[1:2:2]
assert (25,) == squares_tuple[4:100]
l = [1, 2, 3]
assert [1, 2, 3, 4, 5] == (l + [4, 5])
x = [1, 999, 3]
x[1] = 2
assert [1, 2, 3] == x

# A repetition too long for the host: str and bytes overflow, the others run out of memory.
huge = 1 << 62
assert_raises(OverflowError, lambda: "ab" * huge, message="repeated string is too long")
assert_raises(OverflowError, lambda: b"ab" * huge, message="repeated bytes are too long")
for value in ([1], (1, 2), bytearray(b"ab")):
    assert_eq(assert_raises(MemoryError, lambda: value * huge).args, ())
items = [1]
assert_eq(assert_raises(MemoryError, items.__imul__, huge).args, ())

# Sorting is stable and orders keys by <, whatever their kinds (25.1.4).
values = [(i * 7919) % 101 for i in range(300)]
by_less = lambda keys: all(not keys[i + 1] < keys[i] for i in range(len(keys) - 1))
for keys in (values, [v / 8 for v in values], [(v % 3, -v) for v in values], [(v % 3,) * (v % 3) for v in values],
             values + [2 ** 70], [(1, 2 ** 70), (1, 2)] + [(v,) for v in values], values + [1.5], [True, 0, 2], []):
    for reverse in (False, True):
        ordered = sorted(keys, reverse=reverse)
        assert_true(by_less(ordered[::-1] if reverse else ordered))
        assert_eq(sorted(ordered), sorted(keys))
pairs = sorted(range(60), key=lambda v: (v % 4, v % 2), reverse=True)
assert_eq(pairs[:5], [3, 7, 11, 15, 19])
assert_eq(sorted(range(30), key=lambda v: (v % 3) / 2)[:4], [0, 3, 6, 9])
