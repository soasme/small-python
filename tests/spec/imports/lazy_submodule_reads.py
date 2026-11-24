# spec: PLS-315 17.5
# description: A lazy import of a dotted name binds its package; reading
# the submodule as the package's attribute, plainly or for a method call,
# imports it then, running its body, which may loop, once; an error the
# body raises propagates from the read.
from harness import *
from lsr_log import log

lazy import lsr_pkg.sub
lazy import lsr_pkg.other
lazy import lsr_pkg.bad
p = lsr_pkg
assert_eq(log, ["pkg"])
assert_eq(p.sub.value, 7)
assert_eq(log, ["pkg", "sub"])
assert_eq(p.sub.f(), "f")
assert_eq(log, ["pkg", "sub"])
assert_raises(TypeError, lambda: p.other(), message="'module' object is not callable")
assert_eq(log, ["pkg", "sub", "other"])
assert_raises(ValueError, lambda: p.bad, message="bad body")
assert_eq(log, ["pkg", "sub", "other", "bad"])
assert_raises(AttributeError, lambda: p.missing, message="module 'lsr_pkg' has no attribute 'missing'")
