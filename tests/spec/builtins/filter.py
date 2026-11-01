# spec: PLS-315 27.1.5
# description: filter() with predicates and None, and StopIteration raised by a predicate.
from harness import *
assert list(filter(lambda x: (x % 2) == 0, [0, 1, 2])) == [0, 2]

# None implies identity
assert list(filter(None, [0, 1, 2])) == [1, 2]

assert type(filter(None, [])) == filter


# test infinite iterator
class Counter(object):
    counter = 0

    def __next__(self):
        self.counter += 1
        return self.counter

    def __iter__(self):
        return self


it = filter(lambda x: (x % 2) == 0, Counter())
assert next(it) == 2
assert next(it) == 4


def predicate(x):
    if x == 0:
        raise StopIteration()
    return True


filtered = list(filter(predicate, [1, 2, 0, 4, 5]))
assert filtered == [1, 2], filtered

# A StopIteration from the predicate ends only that call; other errors propagate.
def stopper(x): raise StopIteration
stopped = filter(stopper, [1, 2])
assert_raises(StopIteration, next, stopped)
assert_eq(list(stopped), [])
def failing(x): raise ValueError("bad")
assert_raises(ValueError, next, filter(failing, [1]), message="bad")
