# spec: PLS-315 25.1.4
# description: A comparison that raises leaves the list holding every item once.
from harness import *

class Fails:
    """Orders by n; the comparison numbered limit raises."""
    count = 0
    limit = -1
    def __init__(self, n):
        self.n = n
    def __lt__(self, other):
        Fails.count += 1
        if Fails.count == Fails.limit:
            raise ZeroDivisionError("compared once too often")
        return self.n < other.n

def shuffled(size, seed):
    items = [Fails(i) for i in range(size)]
    for i in range(size - 1, 0, -1):
        seed = (seed * 1103515245 + 12345) % 2147483648
        j = seed % (i + 1)
        items[i], items[j] = items[j], items[i]
    return items

def holds_each_once(before, after):
    return len(before) == len(after) and sorted(id(x) for x in before) == sorted(id(x) for x in after)

# Sizes below, at and past one run, so that a failure can come while a run is
# found, while it grows by insertion, or while runs merge.
for size in (2, 5, 31, 32, 33, 64, 100, 257):
    for seed in (1, 7):
        for reverse in (False, True):
            original = shuffled(size, seed)
            Fails.count, Fails.limit = 0, -1
            data = original[:]
            data.sort(reverse=reverse)
            total = Fails.count
            for limit in sorted({1, total // 3, total // 2, total - 1, total} - {0}):
                data = original[:]
                Fails.count, Fails.limit = 0, limit
                assert_raises(ZeroDivisionError, data.sort, reverse=reverse)
                assert holds_each_once(original, data), (size, seed, reverse, limit)
                data = original[:]
                Fails.count = 0
                assert_raises(ZeroDivisionError, data.sort, key=lambda x: x, reverse=reverse)
                assert holds_each_once(original, data), ("key", size, seed, reverse, limit)
Fails.limit = -1

# Keys that refuse to compare leave the items too.
data = [3, "a", 1, 2]
assert_raises(TypeError, data.sort)
assert sorted(data, key=repr) == sorted([3, "a", 1, 2], key=repr)
