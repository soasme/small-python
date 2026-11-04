# spec: PLS-315 25.1.4
# description: Pairs of ints sort by their first item, then their second, stably, at every span.
from harness import *

def pseudo(seed, count):
    out = []
    for _ in range(count):
        seed = (seed * 6364136223846793005 + 1442695040888963407) % 2 ** 64
        out.append(seed >> 33)
    return out

def check(firsts, seconds):
    # Each record carries its index, so equal keys show whether the sort was stable.
    records = [(i, (a, b)) for i, (a, b) in enumerate(zip(firsts, seconds))]
    for reverse in (False, True):
        result = sorted(records, key=lambda r: r[1], reverse=reverse)
        assert len(result) == len(records)
        for x, y in zip(result, result[1:]):
            a, b = (y, x) if reverse else (x, y)
            assert a[1] < b[1] or (a[1] == b[1] and x[0] < y[0]), (x, y, reverse)
        values = [r[1] for r in records]
        values.sort(reverse=reverse)
        assert values == [r[1] for r in result]

big = 2 ** 63
cases = [
    ([n % 7 for n in pseudo(1, 300)], [n % 5 for n in pseudo(2, 300)]),            # Narrow spans, many ties.
    ([n % 3 - 1 for n in pseudo(3, 300)], [-n for n in pseudo(4, 300)]),           # Negative items.
    ([n - big // 2 for n in pseudo(5, 300)], [n % 2 for n in pseudo(6, 300)]),     # A wide first item.
    ([n % 2 for n in pseudo(7, 300)], [n - big // 2 for n in pseudo(8, 300)]),     # A wide second item.
    ([0, 0, 1, 1, -1] * 20, [-big, big - 1, 0, -big, big - 1] * 20),               # The second spans every int64.
    ([-big, big - 1, 0] * 30, [1, 0, 1] * 30),                                      # The first spans every int64.
    ([5] * 50, [3] * 50),                                                          # All equal.
]
for firsts, seconds in cases:
    check(firsts, seconds)

# An int past 64 bits among the pairs still compares exactly.
data = [(1, 2 ** 70), (1, -(2 ** 70)), (0, 5), (1, 0)]
assert sorted(data) == [(0, 5), (1, -(2 ** 70)), (1, 0), (1, 2 ** 70)]
