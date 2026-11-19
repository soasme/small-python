# spec: PLS-315 27.1.1, 9.3.2
# description: An intrinsic iterator's __reduce__ looks its builtins entry
# up by key equality, which calls a stored key's __eq__ (and the reflected
# method after NotImplemented) and goes on with its truth: the iterator's
# state is read after the lookup, but a dict or set iterator's items and a
# range iterator's range before it. An __eq__ that changes the namespace
# restarts the lookup; one that raises propagates; no equal key leaves an
# AttributeError naming the entry.
from harness import *

builtins = vars(iter.__self__)
log = []

class Key:
    def __init__(self, name, effect, answer=None):
        self.name, self.effect, self.answer = name, effect, answer
    def __hash__(self):
        return hash(self.name)
    def __eq__(self, other):
        log.append(("eq", type(other).__name__))
        self.effect()
        return self.answer if self.answer is not None else other == self.name

def reduce_with(name, it, effect, answer=None):
    original = builtins.pop(name)
    builtins[Key(name, effect, answer)] = original
    try:
        return it.__reduce__()
    finally:
        for key in [key for key in builtins if type(key) is Key]:
            del builtins[key]
        builtins[name] = original

def nothing():
    pass

# The state is read after the lookup's __eq__ ran.
it = iter([1, 2, 3])
assert_eq(reduce_with("iter", it, lambda: next(it)), (iter, ([1, 2, 3],), 1))
it = iter("xyz")
assert_eq(reduce_with("iter", it, lambda: list(it)), (iter, ("",)))
it = iter([4, 5]).__next__
callable_it = iter(it, 9)
assert_eq(reduce_with("iter", callable_it, lambda: list(callable_it)), (iter, ((),)))
rev = reversed([1, 2])
assert_eq(reduce_with("reversed", rev, lambda: next(rev)), (reversed, ([1, 2],), 0))

# A dict or set iterator's items, and a range iterator's range, come first.
it = iter({1: 2, 3: 4})
assert_eq(reduce_with("iter", it, lambda: list(it)), (iter, ([1, 3],)))
it = iter({7})
assert_eq(reduce_with("iter", it, lambda: list(it)), (iter, ([7],)))
it = iter(range(0, 10, 3))
assert_eq(reduce_with("iter", it, lambda: next(it)), (iter, (range(0, 12, 3),), None))
it = iter(range(2 ** 70, 2 ** 70 + 2))
assert_eq(reduce_with("iter", it, lambda: next(it)), (iter, (range(2 ** 70, 2 ** 70 + 2),), None))

# The __eq__ result's truth decides; NotImplemented falls to str's, which declines too.
log.clear()
assert_eq(reduce_with("iter", iter(()), nothing, answer=1), (iter, ((), ), 0))
assert_eq(log, [("eq", "str")])
e = assert_raises(AttributeError, reduce_with, "iter", iter(()), nothing, answer=NotImplemented)
assert_eq(e.args, ("iter",))
e = assert_raises(AttributeError, reduce_with, "iter", iter(()), nothing, answer=0)
assert_eq(e.args, ("iter",))

# An error from __eq__, or its truth, propagates.
def fail():
    raise LookupError("eq")
e = assert_raises(LookupError, reduce_with, "iter", iter(()), fail)
assert_eq(e.args, ("eq",))
class Untrue:
    def __bool__(self):
        raise ValueError("bool")
e = assert_raises(ValueError, reduce_with, "iter", iter(()), nothing, answer=Untrue())
assert_eq(e.args, ("bool",))

# An __eq__ that changes the namespace restarts the lookup.
def restore():
    for key in [key for key in builtins if type(key) is Key]:
        del builtins[key]
    builtins["iter"] = iter_builtin
iter_builtin = iter
log.clear()
assert_eq(reduce_with("iter", iter([0]), restore, answer=False), (iter_builtin, ([0],), 0))
assert_eq(log, [("eq", "str")])

# A reduction in a function, as a method or from the class.
def reduced(it):
    return reduce_with("iter", it, lambda: next(it)), type(it).__reduce__(it)
it = iter((5, 6, 7))
assert_eq(reduced(it), ((iter, ((5, 6, 7),), 1), (iter, ((5, 6, 7),), 1)))
