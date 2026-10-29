# build:
# bundles: star_all.py pkg/__init__.py pkg/sub.py
# description: from PKG import * imports the submodules a literal __all__ names, and no others.
from pkg import *
assert sub.X == 2 and VALUE == 1
try:
    other
except NameError:
    other = None
assert other is None
