# spec: PLS-315 25.1.4
# description: Float keys sort in order and stably, both ways; the zeros are equal keys.
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
        assert [repr(k) for k in plain] == [repr(k) for _, k in result]

inf = float("inf")
for size in (0, 1, 2, 100, 600, 3000):
    raw = pseudo(size + 3, size)
    check([n / 2 ** 64 - 0.5 for n in raw])                         # Fractions of both signs.
    check([(n % 1000 - 500) * 1e300 for n in raw])                  # Some overflow to infinities.
    check([(n % 7 - 3) * 5e-324 for n in raw])                      # Subnormals and both zeros.
    check([[0.0, -0.0, 1.5, -inf, inf][n % 5] for n in raw])        # Equal zeros keep their order.
    check([float(n % 9) for n in raw])                              # Few distinct keys.

# With a NaN among them, every key is still there once.
nan = float("nan")
data = [3.0, nan, 1.0, -2.0, nan, 0.5] * 100
result = sorted(data)
assert len(result) == len(data)
assert sum(1 for x in result if x != x) == 200
assert sorted(x for x in result if x == x) == sorted(x for x in data if x == x)
