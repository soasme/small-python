# spec: PLS-315 17.5
# description: A lazy import of a dotted name binds its first part. With
# a Python __import__ in the builtins, reading that name calls it once
# with the whole dotted name, the looking frame's globals and a None
# fromlist, which runs the package and the submodule; with the builtin
# __import__, the read runs only the package, and the submodule runs when
# its attribute is first read.
from harness import assert_eq
OUT = []
def emit(*a):
    OUT.append(' '.join(str(x) for x in a))
import builtins
from ldh_log import log
real = builtins.__import__
def hook(name, globals=None, locals=None, fromlist=(), level=0):
    if name.startswith('ldh_'): log.append(('hook', name, fromlist, level, globals is module_globals))
    return real(name, globals, locals, fromlist, level)
module_globals = globals()
builtins.__import__ = hook
lazy import ldh_one.sub
p = ldh_one
emit(p.__name__, log[:])
emit(p.sub.value, log[:])
builtins.__import__ = real
del log[:]
lazy import ldh_two.sub
q = ldh_two
emit(q.__name__, log[:])
emit(q.sub.value, log[:])
EXPECTED = [
    "ldh_one [('hook', 'ldh_one.sub', None, 0, True), ('hook', 'ldh_log', ('log',), 0, False), 'ldh_one', ('hook', 'ldh_log', ('log',), 0, False), 'ldh_one.sub']",
    "ldh_one [('hook', 'ldh_one.sub', None, 0, True), ('hook', 'ldh_log', ('log',), 0, False), 'ldh_one', ('hook', 'ldh_log', ('log',), 0, False), 'ldh_one.sub']",
    "ldh_two ['ldh_two']",
    "ldh_two ['ldh_two', 'ldh_two.sub']",
]
assert_eq(len(OUT), len(EXPECTED))
for got, want in zip(OUT, EXPECTED):
    assert_eq(got, want)
