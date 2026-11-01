# spec: PLS-315 17.5
# description: Reification calls __import__ with the looking frame's globals and a one-name fromlist; re-entering it is an ImportCycleError.
from harness import *
import builtins

real = builtins.__import__
calls = []
def hook(name, globals=None, locals=None, fromlist=(), level=0):
    if name.startswith("spec_lazy_"):
        calls.append((fromlist, globals is module_globals, locals is module_globals, level))
        if name == "spec_lazy_pair" and len(calls) == 1:
            try:
                eval("spec_lazy_pair", globals)
            except ImportError as error:
                calls.append((type(error).__name__, str(error), error.name))
    return real(name, globals, locals, fromlist, level)
module_globals = globals()
builtins.__import__ = hook
lazy import spec_lazy_pair
assert_eq(spec_lazy_pair.value, 1)
# A loaded module's attribute is bound at once; otherwise reification imports only the name used.
lazy from spec_lazy_pair import other
lazy from spec_lazy_names import value, other as named
assert_eq((other, named), (2, 4))
builtins.__import__ = real
assert_eq(calls, [(None, True, True, 0),
                  ("ImportCycleError", "cannot import name 'spec_lazy_pair' (most likely due to a circular import)", "spec_lazy_pair"),
                  (("other",), True, True, 0)])
