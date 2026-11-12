# spec: PLS-315 27.1.7
# description: reversed() of sequences and __reversed__.
from harness import *
assert list(reversed(range(5))) == [4, 3, 2, 1, 0]

l = [5, 4, 3, 2, 1]
assert list(reversed(l)) == [1, 2, 3, 4, 5]

# The sequence protocol of a type without __reversed__: a memoryview, and a class whose metaclass defines it.
assert list(reversed(memoryview(b"abc"))) == [99, 98, 97]
assert list(reversed(memoryview(b"abcd").cast("H"))) == list(memoryview(b"abcd").cast("H"))[::-1]
class Meta(type):
    def __len__(cls):
        return 2
    def __getitem__(cls, i):
        return i * 10
class Seq(metaclass=Meta):
    pass
assert list(reversed(Seq)) == [10, 0]
