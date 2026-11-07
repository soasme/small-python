# spec: PLS-315 19.3.34
# description: sorted() and list.sort() of strs order them as < does,
# code point by code point with a prefix first, stably, with keys and in
# reverse; strs sharing their first eight characters, NULs, non-ASCII
# text and strs of thousands of characters included.
from harness import *

def insertion_sort(items, key=lambda x: x, reverse=False):
    out = []
    for item in items:
        i = len(out)
        if reverse:
            while i and key(out[i - 1]) < key(item): i -= 1
        else:
            while i and key(item) < key(out[i - 1]): i -= 1
        out.insert(i, item)
    return out

seed = 12345
def rnd():
    global seed
    seed = (seed * 1103515245 + 12345) % 2147483648
    return seed

pieces = ["a", "b", "\x00", "é", "€", "𝄞", "ab", "abcdefgh", "abcdefghi", "Z", "", "abcdefg\x00"]
words = ["".join(pieces[rnd() % len(pieces)] for _ in range(rnd() % 5)) for _ in range(400)]
assert_eq(sorted(words), insertion_sort(words))
assert_eq(sorted(words, reverse=True), insertion_sort(words, reverse=True))
order = list(range(len(words)))
assert_eq(sorted(order, key=lambda i: words[i]), insertion_sort(order, key=lambda i: words[i]))
assert_eq(sorted(order, key=lambda i: words[i], reverse=True),
          insertion_sort(order, key=lambda i: words[i], reverse=True))
copy = list(words)
copy.sort()
assert_eq(copy, sorted(words))
long = ["x" * 5000 + "b", "x" * 5000 + "a", "x" * 4095, "x" * 4096, "a", "x" * 4095 + "a"]
assert_eq(sorted(long), insertion_sort(long))
assert_eq(sorted(["abcdefgh", "abcdefgh\x00", "abcdefg", "abcdefgh"]), ["abcdefg", "abcdefgh", "abcdefgh", "abcdefgh\x00"])
