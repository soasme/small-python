# spec: reference/import.html
# description: import, from-import, packages, relative imports, namespace packages, caching, errors, __all__, PEP 562 and PEP 810.
from harness import *

def write(path, text):
    with open(path, "w") as f:
        f.write(text)

# The test's own directory is on the import path.
write("spec_mod.py", "value = 1\ncount = 0\n_private = 2\ndef f(): return __name__\n")
import spec_mod
assert_eq(spec_mod.value, 1)
assert_eq(spec_mod.f(), "spec_mod")
assert_eq(spec_mod.__name__, "spec_mod")
assert_true(spec_mod.__file__.endswith("spec_mod.py"))
assert_eq(type(spec_mod).__name__, "module")
spec_mod.count += 1
import spec_mod as again
assert_is(again, spec_mod)
assert_eq(again.count, 1)
from spec_mod import value as v, f
assert_eq((v, f()), (1, "spec_mod"))
ns = run("from spec_mod import *\n")
assert_true("value" in ns and "_private" not in ns)

write("spec_all.py", "__all__ = ['b']\na = 1\nb = 2\n_c = 3\n")
ns = run("from spec_all import *\n")
assert_true("b" in ns and "a" not in ns)
write("spec_bad_all.py", "__all__ = ['missing']\n")
assert_raises(AttributeError, run, "from spec_bad_all import *\n")

e = assert_raises(ModuleNotFoundError, run, "import spec_no_such_module\n")
assert_eq(e.name, "spec_no_such_module")
assert_eq(str(e), "No module named 'spec_no_such_module'")
e = assert_raises(ImportError, run, "from spec_mod import nothing_here\n")
assert_eq(e.name, "spec_mod")
assert_true(str(e).startswith("cannot import name 'nothing_here' from 'spec_mod'"))
assert_syntax_error("def g():\n    from spec_mod import *\n")
assert_syntax_error("class C:\n    from spec_mod import *\n")
assert_syntax_error("import a.b as\n")
assert_syntax_error("from . import a, b,\n")
assert_syntax_error("import (a)\n")
assert_syntax_error("from x import (*)\n")
assert_compiles("from . import (a, b,)\n")
assert_compiles("from .... import a\n")
assert_raises(ImportError, run, "from . import x\n", {"__name__": "__main__"})

# A module that raises during import is not left in a usable state.
assert_raises(ValueError, run, "import spec_raises\n")
assert_raises(ValueError, run, "import spec_raises\n")

# Packages: __init__ runs first, then submodules; relative imports.
import spec_pkg
assert_eq(spec_pkg.order, ["pkg", "sub"])
assert_eq(spec_pkg.helper(), ("spec_pkg.sub", "spec_pkg"))
assert_is(spec_pkg.sub, spec_pkg.sub)
assert_eq(spec_pkg.__package__, "spec_pkg")
assert_true(hasattr(spec_pkg, "__path__"))
import spec_pkg.subpkg.deep
assert_eq(spec_pkg.subpkg.deep.name, "spec_pkg.subpkg.deep")
assert_eq(spec_pkg.subpkg.deep.package, "spec_pkg.subpkg")
assert_eq(spec_pkg.subpkg.deep.sibling.value, "sibling")
assert_is(spec_pkg.subpkg.deep.sub, spec_pkg.sub)
from spec_pkg.subpkg import sibling
assert_eq(sibling.value, "sibling")
import spec_pkg.subpkg.deep as deep_alias
assert_eq(deep_alias.name, "spec_pkg.subpkg.deep")
ns = run("import spec_pkg.sub\n")
assert_is(ns["spec_pkg"], spec_pkg)
e = assert_raises(ImportError, run, "import spec_pkg.beyond\n")
assert_eq(str(e), "attempted relative import beyond top-level package")
assert_raises(ModuleNotFoundError, run, "import spec_mod.sub\n")

# Namespace packages have no __init__ and no __file__.
import spec_ns.inner.leaf
assert_true(spec_ns.inner.leaf.leaf)
assert_is(getattr(spec_ns, "__file__", None), None)

# Circular imports see the partially initialized module.
import spec_cycle_a
import spec_cycle_b
assert_false(spec_cycle_b.partial)
assert_eq(spec_cycle_a.from_b(), "b")

# PEP 562: module __getattr__ and __dir__.
import spec_getattr
assert_eq(spec_getattr.dynamic, 42)
assert_raises(AttributeError, lambda: spec_getattr.missing)
assert_eq(dir(spec_getattr), ["dynamic", "listed"])
from spec_getattr import dynamic
assert_eq(dynamic, 42)

# PEP 810: lazy imports load on first use of the name.
import spec_lazy_log
lazy import spec_lazy_target
assert_eq(spec_lazy_log.events, [])
assert_eq(spec_lazy_target.attr, "lazy value")
assert_eq(spec_lazy_log.events, ["loaded"])
lazy from spec_mod import value as lazy_value
assert_eq(lazy_value, 1)
assert_syntax_error("def f():\n    lazy import x\n")
assert_syntax_error("class C:\n    lazy import x\n")
assert_syntax_error("try:\n    lazy import x\nexcept: pass\n")
assert_syntax_error("lazy from x import *\n")
assert_syntax_error("lazy from __future__ import annotations\n")
lazy = "soft keyword"
assert_eq(lazy, "soft keyword")
