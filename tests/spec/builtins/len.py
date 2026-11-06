# spec: PLS-315 19.3.24, 7.5.2
# description: len() and __len__ results: a Python __len__ that loops,
# called inside functions, returns an index that is not negative.
from harness import *
assert 3 == len([1, 2, 3])
assert 2 == len((1, 2))

class Sized:
    def __init__(self, n): self.n = n
    def __len__(self):
        for _ in range(2): pass
        return self.n
class Indexed:
    def __index__(self): return 4
class Inherited(Sized): pass
def lengths():
    results = [len(Sized(3)), len(Sized(True)), len(Sized(Indexed())), len(Inherited(5))]
    for n, error in (("a", TypeError), (-1, ValueError), (2 ** 64, OverflowError)):
        try:
            len(Sized(n))
        except error as e:
            results.append(str(e))
    try:
        len(Indexed())
    except TypeError as e:
        results.append(str(e))
    return results
assert_eq(lengths(), [3, 1, 4, 5, "'str' object cannot be interpreted as an integer",
                      "__len__() should return >= 0", "cannot fit 'int' into an index-sized integer",
                      "object of type 'Indexed' has no len()"])
