# build: -I lib
# bundles: search_order.py shadow.py both/__init__.py nsmod.py pkg/__init__.py
# description: the first root that has a name wins; in one directory a package beats a module and a module beats a namespace directory; a regular package's submodules come only from its own directory.
import shadow
import both
import nsmod
import pkg
assert shadow.KIND == "module"
assert both.KIND == "package"
assert nsmod.KIND == "module"
try:
    import pkg.extra
except ImportError:
    extra = None
else:
    extra = pkg.extra
assert extra is None
