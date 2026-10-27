# spec: library/functions.html#all
# description: all() short-circuits and propagates errors from truth tests and iteration.
from harness import *

assert all([True])
assert not all([False])
assert all([])
assert not all([False, TestFailingBool()])

assert_raises(RuntimeError, all, TestFailingIter())
assert_raises(RuntimeError, all, [TestFailingBool()])
