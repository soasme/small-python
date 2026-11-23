# spec: PLS-315 17.5
# description: Resolving a placeholder resolves a placeholder in its turn:
# one that __import__ returns, and one that the imported name is bound to
# on the object __import__ returns.
from harness import *
import builtins

real = builtins.__import__
lazy import spec_nested_third
held = [globals()["spec_nested_third"]]
class Holder: pass
holder = Holder()
holder.name = held[0]
def hook(name, *args):
    if name == "spec_nested_fake":
        return held[0]
    if name == "spec_nested_holder":
        return holder
    return real(name, *args)
builtins.__import__ = hook
lazy import spec_nested_fake
assert_eq(spec_nested_fake.x, 9)
lazy from spec_nested_holder import name
assert_eq(name.x, 9)
builtins.__import__ = real

# A module's placeholder attribute is reified as it is imported.
lazy from spec_nested_outer import spec_nested_inner as inner
assert_eq(inner.value, 7)
