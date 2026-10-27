# spec: library/functions.html#any
# description: any() short-circuits and propagates errors from truth tests and iteration.
from harness import *

assert any([True])
assert not any([False])
assert not any([])
assert any([True, TestFailingBool()])

assert_raises(RuntimeError, lambda: any(TestFailingIter()))
assert_raises(RuntimeError, lambda: any([TestFailingBool()]))
