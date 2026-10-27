# spec: PLS-315 19.3.3
# description: any() short-circuits and propagates errors from truth tests and iteration.
from harness import *

assert any([True])
assert not any([False])
assert not any([])
assert any([True, TestFailingBool()])

assert_raises(RuntimeError, lambda: any(TestFailingIter()))
assert_raises(RuntimeError, lambda: any([TestFailingBool()]))
