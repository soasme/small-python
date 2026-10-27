# spec: PLS-315 29.8, 17.5
# description: The placeholders lazy imports bind, their repr, resolve(), and failures during resolution.
from harness import *

# A placeholder is read through globals(); binding it to another global name
# would reify it at the next lookup of that name (17.5), so it is kept in a list.
lazy from spec_lazy_ok import value
assert_eq(repr(globals()["value"]), "<lazy_import 'spec_lazy_ok.value'>")

lazy import spec_lazy_ok
held = [globals()["spec_lazy_ok"]]
LazyImportType = type(held[0])
assert_eq(LazyImportType.__name__, "lazy_import")
assert_eq(LazyImportType.__module__, "builtins")
assert_eq(repr(held[0]), "<lazy_import 'spec_lazy_ok'>")
e = assert_raises(TypeError, LazyImportType)
assert_eq(str(e), "cannot create 'lazy_import' instances")
with assert_raises(TypeError):
    class Sub(LazyImportType):
        pass
# resolve() imports without rebinding the name.
module = held[0].resolve()
assert_eq(module.value, "loaded")
assert_is(globals()["spec_lazy_ok"], held[0])
# Reification by use rebinds it.
assert_eq(spec_lazy_ok.value, "loaded")
assert_is(globals()["spec_lazy_ok"], module)
# Any global name bound to a placeholder reifies when looked up.
lazy import spec_lazy_ok as again
alias = globals()["again"]
assert_is(alias, module)
assert_is(globals()["alias"], module)
assert_eq(value, "loaded")


lazy import spec_lazy_broken
held = [globals()["spec_lazy_broken"]]
e = assert_raises(ValueError, held[0].resolve)
assert_eq(str(e), "broken module")
assert_type(e.__cause__, ImportError)
assert_eq(str(e.__cause__), "lazy import of 'spec_lazy_broken' raised an exception during resolution")
e = assert_raises(ValueError, lambda: spec_lazy_broken.anything)
assert_eq(str(e.__cause__), "lazy import of 'spec_lazy_broken' raised an exception during resolution")
# A failed reification leaves the placeholder bound.
assert_eq(type(globals()["spec_lazy_broken"]).__name__, "lazy_import")
