# spec: PLS-315 25.1.4
# description: Int keys sort in order and stably, both ways, at every size and span.
from harness import *

def pseudo(seed, count):
    out = []
    for _ in range(count):
        seed = (seed * 6364136223846793005 + 1442695040888963407) % 2 ** 64
        out.append(seed)
    return out

def check(keys):
    # Each record carries its index, so equal keys show whether the sort was stable.
    records = list(enumerate(keys))
    for reverse in (False, True):
        result = sorted(records, key=lambda r: r[1], reverse=reverse)
        assert sorted(i for i, _ in result) == list(range(len(keys)))
        for x, y in zip(result, result[1:]):
            a, b = (y, x) if reverse else (x, y)
            assert a[1] < b[1] or (a[1] == b[1] and x[0] < y[0]), (x, y, reverse)
        plain = sorted(keys, reverse=reverse)
        assert plain == [k for _, k in result]

big = 2 ** 63
for size in (0, 1, 2, 63, 64, 65, 300, 2000):
    raw = pseudo(size + 1, size)
    check([n % 3 for n in raw])                 # Few distinct keys.
    check([n % 100003 - 50000 for n in raw])    # Negative and positive.
    check([n >> 1 for n in raw])                # Most of the int64 range.
    check([n - big for n in raw])               # All of it.
    check(list(range(size)))                    # In order already.
    check(list(range(size, 0, -1)))             # Reversed.
    check([7] * size)                           # All equal.
