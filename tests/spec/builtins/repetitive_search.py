# spec: PLS-315 23.1.4, 23.1.5, 24.3
# description: searching repetitive text finds the lowest and highest occurrences, as count and replace see them.
from harness import *

for N in (1000, 3000):
    A, B = "a" * N, "b" * N
    haystack = A + A + B + A + A
    needle = A + B + B + A
    for kind in (str, lambda s: s.encode(), lambda s: bytearray(s, "ascii")):
        h, n = kind(haystack), kind(needle)
        assert_eq((h.find(n), h.rfind(n), h.count(n)), (-1, -1, 0))
        assert_eq(((h + n).find(n), (h + n).count(n)), (len(h), 1))
        assert_eq(((n + h).rfind(n), (n + h + n).rfind(n)), (0, len(n) + len(h)))
    # A periodic needle: the text repeats it with one byte changed.
    needle = "ab" * N
    haystack = ("ab" * (N - 1) + "b") * 2
    assert_eq((haystack.find(needle), haystack.rfind(needle), haystack.count(needle)), (-1, -1, 0))
    # needle + haystack begins with "ab" * (2N - 1), so the last match starts at 2N - 2.
    assert_eq(((haystack + needle).find(needle), (needle + haystack).rfind(needle)), (len(haystack), 2 * N - 2))
    assert_eq((haystack + needle + haystack).replace(needle, "|"), haystack + "|" + haystack)
    assert_eq((haystack + needle + "x").split(needle), [haystack, "x"])

# Every candidate ends like the pattern, so matches far from the start are
# reached only after many near misses.
pattern = "b" + "a" * 40
for k in range(0, 300, 7):
    text = "a" * k + pattern + "a" * k
    assert_eq((text.find(pattern), text.rfind(pattern), text.count(pattern)), (k, k, 1))
    mirror = text[::-1]
    assert_eq(mirror.rfind(pattern[::-1]), len(text) - k - len(pattern))
